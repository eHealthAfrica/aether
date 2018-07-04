# aether-website

This is the product website for aether.
It uses Jekyll for site generation. 
This allows us to use Markdown to easily add and update documentation and blog posts.

## documentation

The files for the documentation can be found in `/documentation`

To write your doc files you can use markdown (we use the kramdown converter: https://kramdown.gettalong.org/quickref.html), but also plain html works fine.

In the header of each file in documentation needs to be the following:

```
  ---
  title: foo
  permalink: documentation/foo.html
  ---
```

The title defines the page title `<title />`
And permalink tells the jekyll site generator where the page should live, which, in our case, is the documentation folder.
 
Once you've added your documentation file, you need to configure the documentation's navigation in order to make the page accessible.

Edit the `list.yml` in `_data`

```
  toc:
    - title: Getting started
      subfolderitems:
        - page: Example Doc
          url: /documentation/example.html
        - page: Lorem ipsum
          url: /documentation/foo.html
```
          
 - the `title` is for subheadings in the documentation's menu.
 - `page` is for the name that is going to be displayed in the menu.
 - `url` is for the path to that document
