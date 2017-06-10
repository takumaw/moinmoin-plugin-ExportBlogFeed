MoinMoin plugin: ExportBlogFeed
===============================

ExportBlogFeed is a MoinMoin plugin that adds MoinMoin a feed exporting action for blogging.

Installation
------------

  1. Copy `ExportBlogFeed.py` to your MoinMoin's `data/plugin/action` directory.
  2. If you don't have `feedparser` module installed, install it.
    * You can install it under `data/plugin/action`.

Usage
-----

  1. Prepare the top page for your blog.
    * e.g. `/Blog`
  2. Write some blog posts under `BLOG_PATH/YYYY-MM-DD`.
    * e.g. `/Blog/2017-04-01`
  3. Run `ExportBlogFeed` action on your blog top page.
  4. That's it!

You can configure blog feed options using `#pragma` directives on your blog top page.

Available options:

  * `#pragma blog-feed-title YOUR BLOG FEED TITLE`
  * `#pragma blog-feed-description YOUR BLOG FEED'S DESCRIPTION`
  * `#pragma blog-feed-link YOUR BLOG'S TOP PAGE URL`
  * `#pragma blog-feed-feed-url YOUR BLOG FEED'S URL`
    * Useful when you use feed distributors like FeedBurner, etc.
  * `#pragma blog-feed-language`
    * You can also specify language via `#language` directive.
  * `#pragma blog-feed-number-of-items`
    * Omit blog posts from your feed older than this value.

  See also: <https://moinmo.in/HelpOnProcessingInstructions>

Copyright and License
---------------------

(C) WATANABE Takuma <takumaw@sfo.kuramae.ne.jp>

License: GPL v2.
