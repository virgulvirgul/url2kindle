`url2kindle-flask` is a tiny Flask application that sends URLs to your Kindle.

The process is build on top of far better projects than this one:

- You make a request to url2kindle with the URL of an article or webpage
- [Mercury Parser][mercury] extracts the content of the page
- [Beautiful Soup][bs] extracts the `<title>` and some other metadata
- The article is rendered as HTML with the [Blitz CSS][blitz] reset
- [`kindlegen`][kindlegen] is used to convert the HTML to a Kindle compatible mobi file
- [Amazon SES][ses] sends the ebook to your @[free.kindle.com][free] email address

_And that all happens within a few seconds, for free, on Heroku_

---

### Configuration

Sign up for [Mercury][mercury] and [SES][ses] then configure by setting the following environment variables in Heroku:

```
heroku config:set MERCURY_KEY=... \
    SMTP_USERNAME=... \
    SMTP_PASSWORD=... \
    SMTP_FROM_EMAIL=... \
    SMTP_TO_EMAIL=...
```