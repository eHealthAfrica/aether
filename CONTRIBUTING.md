# Introduction

### You want to help out with Aether? Yay!

First off, thank you for considering contributing to Aether. It's people like you that make Aether *the* platform for data-driven humanitarian projects.

## How you can help

Aether is an open source project and we love to receive contributions from our community. There are many ways to contribute, from writing tutorials or blog posts, improving the documentation, submitting bug reports and feature requests or writing code which can be incorporated into Aether itself. 

If you decide that you want to help out with development, you should start by getting Aether installed locally. Follow the [guide](https://aether.ehealthafrica.org/documentation/try/index.html) on the Aether website (and of course, if you have any problems following that guide, or you think it could be improved in any way, feel free to open and issue!). Once you’ve got Aether running and you’ve got a feel for the fundamental concepts and architecture, then you can dive right in and start writing code.

At any point, you can get help on the [Aether forum](https://forums.ehealthafrica.org/c/aether).

Our [Jira board](https://jira.ehealthafrica.org/secure/RapidBoard.jspa?rapidView=161&view=planning.nodetail&epics=visible) shows a list of the bugs and features that are currently in our roadmap; you might want to look through them to get a sense of where we’re heading in the near future. You might even want to pick one of them and get to work; if so, fantastic! Get in touch with us on the forum and we can help you figure out the best way to approach the work.

If you find a bug that you want to report, or a feature that you think Aether needs, start by opening and issue on the repo. We can then check it, discuss it with you and ensure that you have added all the required information. Once that’s all done, we will promote the issue to the Jira backlog – at which point you are of course very welcome to start working on it yourself!

## How to report a bug

If you find a security vulnerability, do NOT open an issue. Email aether@ehealthafrica.org instead.

In order to determine whether you are dealing with a security issue, ask yourself these two questions:
- Can I access something that's not mine, or something I shouldn't have access to?
- Can I disable something for other people?

If the answer to either of those two questions are "yes", then you're probably dealing with a security issue. Note that even if you answer "no" to both questions, you may still be dealing with a security issue, so if you're unsure, just email us.

When you file an issue, please ensure that you have answered every question in the issue template.

## Getting started with Aether developement

### Fork and clone the repository
You will need to fork the main Aether repository and clone it to your local machine. See [github help page](https://help.github.com/articles/fork-a-repo) for help.

### Submitting your changes
Once your changes and tests are ready to submit for review:

1. Test your changes

Run the test suite to make sure that nothing is broken. See the main [README](README.md) file for help running tests.

### Sign the Contributor License Agreement

Please make sure you have signed our Contributor License Agreement. We are not asking you to assign copyright to us, but to give us the right to distribute your code without restriction. We ask this of all contributors in order to assure our users of the origin and continuing existence of the code. You only need to sign the CLA once.

### Rebase your changes

Update your local repository with the most recent code from the main Aether repository, and rebase your branch on top of the latest `develop` branch. We prefer your initial changes to be squashed into a single commit. Later, if we ask you to make changes, add them as separate commits. This makes them easier to review. As a final step before merging we will either ask you to squash all commits yourself or we'll do it for you.

Note that we prefer to use [semantic commit messages](https://seesparkbox.com/foundry/semantic_commit_messages), both for commit message and for PR title.

### Submit a pull request

Push your local changes to your forked copy of the repository and submit a pull request. In the pull request, choose a title which sums up the changes that you have made, adhering to the semantic commit message format linked to above, and in the body provide more details about what your changes do. Also mention the number of the issue where discussion has taken place, eg "Closes #123".

Then sit back and wait. There will probably be discussion about the pull request and, if any changes are needed, we would love to work with you to get your pull request merged into Aether.

Please adhere to the general guideline that you should never force push to a publicly shared branch. Once you have opened your pull request, you should consider your branch publicly shared. Instead of force pushing you can just add incremental commits; this is generally easier on your reviewers. If you need to pick up changes from develop, you can merge develop into your branch. A reviewer might ask you to rebase a long-running pull request in which case force pushing is okay for that request. Note that squashing at the end of the review process should also not be done, that can be done when the pull request is integrated via GitHub.

### Developing a custom consumer

One of the most obvious areas for extension within Aether is the consumers, which read data from Kafka and then write it to some other destination. If you want to use the Aether platform in your project, you will probably find that you need to build a custom consumer. If so, that’s great! Consumers can be written in any language you like - we use Python, but it’s entirely up to you.

Examples of consumers that are in our roadmap are:

- a relational DB consumer to land data as rows in arbitrary, configurable databases
- a Rest API consumer that can submit data to arbitrary, configurable endpoints
- a DHIS2 consumer

Consumers don’t live in the core Aether repo; the best thing you can do is to put your custom consumer into its own repo in your organisation. If however you think that your consumer would be useful for the wider Aether community, we’d love to discuss possibilities for how we can bring it into the Aether ecosystem.

## This is step 1

To get started, <a href="https://www.clahub.com/agreements/eHealthAfrica/aether">sign the Contributor License Agreement</a>.
