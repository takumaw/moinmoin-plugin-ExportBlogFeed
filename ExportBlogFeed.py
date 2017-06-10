# -*- coding: utf-8 -*-
"""
    MoinMoin - ExportBlogFeed action
    @copyright: 2017 WATANABE Takuma <takumaw@sfo.kuramae.ne.jp>
"""

import datetime
import re
import copy

import MoinMoin
import MoinMoin.Page
import MoinMoin.action
import MoinMoin.action.cache
import MoinMoin.caching
import MoinMoin.parser.text_moin_wiki
import MoinMoin.search
import MoinMoin.web.contexts
import MoinMoin.web.request
import MoinMoin.wikiutil
import feedgenerator

__version__ = "0.1.0"

action_name = __name__.split('.')[-1]
Dependencies = ['page']


# Static variables

FEED_CONF_DEFAULT = {
    'blog-feed-title': u'',
    'blog-feed-description': u'',
    'blog-feed-link': u'',
    'blog-feed-feed-url': u'',
    'blog-feed-language': u'',
    'blog-feed-number-of-items': 10,
}


# Action invocation function

def execute(pagename, request):
    """Process a request"""

    _ = request.getText

    # check whether a user has an access to the page

    if not request.user.may.read(request.page.page_name):
        request.mimetype = 'text/plain'
        request.write(_("This page no longer allows read access."))
        return

    # check whether a cache for the page is available

    page = MoinMoin.Page.Page(request, request.page.page_name)

    cache_key_content = "%s-%s" % (page.get_real_rev(),
                                   datetime.datetime.utcnow())
    cache_key = MoinMoin.action.cache.key(request, content=cache_key_content)
    cache_entry = MoinMoin.caching.CacheEntry(
        request, page, cache_key, scope="item")

    if cache_entry.exists():
        # retrieve cache entry
        cache_entry.open()
        try:
            content = cache_entry.read()
        finally:
            cache_entry.close()
    else:
        # build the content and cache it
        content = _generate_blog_feed(request)
        cache_entry.open(mode="w")
        try:
            try:
                cache_entry.write(content)
            finally:
                cache_entry.close()
        except IOError:
            if cache_entry.exists():
                cache_entry.remove()

    # write the content to the request/response.

    request.mimetype = 'application/atom+xml'
    request.write(content)
    return


# Private helper methods

def _generate_blog_feed(request):
    """Send the blog RSS to the processor."""

    feed_conf = _parse_feed_config(request)
    feed = _build_feed(request, feed_conf)
    _add_feed_items(request, feed, feed_conf)
    content = feed.writeString("utf-8")
    return content


def _parse_feed_config(request):
    """Parse the feed configuration."""

    request_page = MoinMoin.Page.Page(request, request.page.page_name)

    feed_conf = copy.deepcopy(FEED_CONF_DEFAULT)

    # parse raw feed configs

    feed_conf_raw = {}

    for ln in request.page.get_raw_body().splitlines():
        if ln.startswith("#pragma"):
            pragma_derective, pragma_key, pragma_value = ln.split(" ", 2)
            if pragma_key in FEED_CONF_DEFAULT:
                feed_conf_raw[pragma_key] = pragma_value

        elif ln.startswith("#language"):
            ln_split = ln.rstrip().split()
            feed_conf_raw["language"] = ln_split[1]

    # parse language

    if feed_conf_raw["language"]:
        if not feed_conf_raw["blog-feed-language"]:
            feed_conf_raw["blog-feed-language"] = feed_conf_raw["language"]
        del feed_conf_raw["language"]

    # parse item limit

    if "blog-feed-number-of-items" in feed_conf_raw:
        try:
            feed_conf_raw["blog-feed-number-of-items"] = int(
                blog_feed_item_limit)
        except ValueError as e:
            del feed_conf_raw["blog-feed-number-of-items"]

    # fill default values if available and not present

    feed_conf.update(feed_conf_raw)

    if not feed_conf["blog-feed-link"]:
        blog_link_dict = {
            "host_url": request.host_url[:-1],
            "url": request_page.url(request),
        }
        blog_feed_link = "%(host_url)s%(url)s" % (blog_link_dict)
        feed_conf["blog-feed-link"] = blog_feed_link

    if not feed_conf["blog-feed-url"]:
        blog_feed_url_dict = {
            "host_url": request.host_url[:-1],
            "url": request_page.url(request),
            "action_name": action_name,
        }
        blog_feed_url = "%(host_url)s%(url)s?action=%(action_name)s" % (
            blog_feed_url_dict)
        feed_conf["blog-feed-url"] = blog_feed_url

    return feed_conf


def _build_feed(request, feed_conf):
    """Build the feed."""

    request_page = MoinMoin.Page.Page(request, request.page.page_name)

    feed = feedgenerator.Rss201rev2Feed(
        title=feed_conf["blog-feed_title"],
        link=feed_conf["blog-feed-link"],
        feed_url=feed_conf["blog-feed-url"],
        description=feed_conf["blog-feed-description"],
        language=feed_conf["blog-feed-language"],
    )

    return feed


def _add_feed_items(request, feed, feed_conf):
    """Build the feed items."""

    blog_post_pages_query = "^%s/[0-9]+-[0-9]+-[0-9]+" % request.page.page_name
    blog_post_pages_search_results = _get_pages_by_query(
        request, blog_post_pages_query, sort=True, reverse=True)
    blog_post_pages_search_results = blog_post_pages_search_results[
        :feed_conf["blog-feed-number-of-items"]]

    for blog_post_pages_search_result in blog_post_pages_search_results:
        blog_post_page = MoinMoin.Page.Page(
            request, blog_post_pages_search_result.page_name)

        blog_post_title_list = re.findall(
            u"^= (.+) =$", blog_post_page.get_raw_body(), re.MULTILINE)
        blog_post_title = " / ".join(blog_post_title_list)

        blog_post_link_dict = {
            "host_url": request.host_url[:-1],
            "url": blog_post_page.url(request),
        }
        blog_post_link = "%(host_url)s%(url)s" % (blog_post_link_dict)

        blog_post_description = _get_page_as_html(request, blog_post_page)

        blog_post_pubdate = datetime.datetime.utcfromtimestamp(
            blog_post_page.mtime_usecs() / 1000000)

        blog_post_unique_id = blog_post_link

        feed.add_item(
            title=blog_post_title,
            link=blog_post_link,
            description=blog_post_description,
            pubdate=blog_post_pubdate,
            unique_id=blog_post_unique_id,
        )


def _get_pages_by_query(request, query, sort=False, reverse=False):
    query_object = MoinMoin.search.QueryParser(regex=True).parse_query(query)
    search_result = MoinMoin.search.searchPages(request, query_object)
    search_result_hits = search_result.hits

    if sort:
        search_result_hits.sort(key=lambda pg: pg.page_name, reverse=reverse)

    return search_result_hits


def _get_page_as_html(request, page):
    page_name = page.page_name
    raw_body = page.get_raw_body()
    pseudo_request = MoinMoin.web.contexts.ScriptContext()
    pseudo_request.formatter.page = MoinMoin.Page.Page(
        pseudo_request, page_name)

    html_body = MoinMoin.wikiutil.renderText(
        pseudo_request, MoinMoin.parser.text_moin_wiki.Parser, raw_body)

    return html_body
