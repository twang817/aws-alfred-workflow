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

Open AWS Web Console
--------------------
You can also open your browser to the AWS Web Console using the `awsweb`
command:

`awsweb <query>`

See [here](https://github.com/rkoval/alfred-aws-console-services-workflow) for demo.

Changelog
=========

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
