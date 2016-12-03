aws-alfred-workflow
===================

AWS workflow for Alfred 3.

This workflow allows you to search EC2 instances by `InstanceId` and by the
`Name` tag.

Install
=======

You must have your AWS credentials set up in your ~/.aws directory:

```bash
$ cd ~/.aws
$ ls -l
total 8
-rw------- 1 twang staff 224 Nov 26 00:28 config
-rw------- 1 twang staff 706 Nov 18 00:01 credentials
$ cat config
[default]
region = us-east-1

[profile foo]
region = us-west-2
$ cat credentials
[default]
aws_access_key_id = xxxxxxxxxxxxxxxxxxxxx
aws_secret_access_key = xxxxxxxxxxxxxxxxxxxxx

[foo]
aws_access_key_id = xxxxxxxxxxxxxxxxxxxxx
aws_secret_access_key = xxxxxxxxxxxxxxxxxxxxx
```

Configuration
=============
In Alfred Preferences, choose the AWS workflow and click the `[x]` icon to
configure the `WF_QUICKLOOK_PORT` environment variable.

![config_demo](https://raw.githubusercontent.com/twang817/aws-alfred-workflow/master/docs/config_env.png)

If not configured, quicklook will be disabled.

Usage
=====

Select AWS Profile
------------------
Select the AWS profile to use via:

`aws >profile <profile name>`


Searching for Instances
-----------------------
Now, you can search your EC2 instances via:

`aws <query>`

* Select an instance to copy the private IP address to your clipboard.
* Hold `alt` to copy public IP address to your clipboard.
* Hold `cmd` to open AWS web console to that instance.
* Press `shift` (or ⌘Y) to open quicklook to view instance details

### Search query

Search queries can be in the form of a space separated list of `facet:value` or
simply just `value`.  Single (`'`) or double (`"`) quotes may be used for either
the `facet` or `value` to allow for spaces,  and escapes (`\\`) can be used to
escape a literal apostrophe or quotation character.  Furthermore, colons in
`facets` and `values` can be specified by quoting the string (e.g.:
`url:'www.august8.net:8080'`).

The available `facets` for each service, as well as the default `facet` if not
provided, is specified for each service below.

#### EC2 facets

If a bare `value` starts with `i-`, the workflow will search for exact prefix
matches against the EC2 Instance Id.  Otherwise, bare `value` queries will
search the `Name` tag for the instance.

All other facets map to the tags on the instance.  Note, all tag names are
converted to lowercase.

#### S3 facets

The default facet is the `Name` tag for the bucket.

All other facets map to the tags on the bucket.  Note, all tag names are
converted to lowercase.

#### Examples

Search for an EC2 Instance with a `Role` tag of `webserver`:

`aws role:web`

If the EC2 Instance also has a `Environment` tag of `integration-testing`,
I can search multiple tags via:

`aws role:web environment:test`

If the EC2 instance also happens to be named `my-test-application`, I may
further restrict my query:

`aws role:web environment:test my te app`

Open AWS Web Console
--------------------
You can also open your browser to the AWS Web Console using the `+` leader
prefix:

`aws +<query>`

See [here](https://github.com/rkoval/alfred-aws-console-services-workflow) for demo.

Changelog
=========

## v3.1.0 - 2016-12-03

### Added
- auto-update, run `aws >update`

### Changed
- fixed help command

## v3.0.0 - 2016-12-03

### Added
- ablity to search s3 buckets

### Changed
- using a subcommand syntax inspired by [gharian/alfred-github-workflow](https://github.com/gharlan/alfred-github-workflow)
- improved responsiveness of the app by using background tasks

## v2.0.0 - 2016-11-27

### Added
- faceted searching

## v1.1.1 - 2016-11-27

### Fixed
- bug where quicklook was not disabled if port was not configured

## v1.1 - 2016-11-27

### Added
- added awsweb command (stolen from https://github.com/rkoval/alfred-aws-console-services-workflow)
- added quicklook server

### Changed
- changed public IP binding to `alt` to not conflict with quicklook


Contributors
============
* [rkoval](https://github.com/rkoval)
