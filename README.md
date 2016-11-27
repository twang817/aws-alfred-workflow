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

`awsprofile <profile name>`


Searching for Instances
-----------------------
Now, you can search your EC2 instances via:

`aws <query>`

* Select an instance to copy the private IP address to your clipboard.
* Hold `alt` to copy public IP address to your clipboard.
* Hold `cmd` to open AWS web console to that instance.
* Press `shift` (or ⌘Y) to open quicklook to view instance details

### Search query

The search query, by default, will search only `InstanceIds` if the query begins
with `i-` and consists of only 1 term.  When searching `InstanceIds` the query
must be an exact prefix match.

If the query does not begin with `i-`, the search will be performed using a
fuzzy match against the name of the instance (via the `Name` tag).

You can also search by other tags by specifying the tag in the form of
`tag:value`.  For example, if I have an EC2 instances with a `Role` tag of
`webserver`, I can use the query: `role:web` to find all instances that have
`webserver` in the `Role` tag.  Note, that tag names are case insensitive.

Additionally, you can combine multiple search terms.  For example, the query:
`role:web environment:test my te app` might find an EC2 instance named
`my-test-application` with a `Role` tag of `webserver` and a `Environment` tag
of `integration-testing`.


Open AWS Web Console
--------------------
You can also open your browser to the AWS Web Console using the `awsweb`
command:

`awsweb <query>`

See [here](https://github.com/rkoval/alfred-aws-console-services-workflow) for demo.

Changelog
=========

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
