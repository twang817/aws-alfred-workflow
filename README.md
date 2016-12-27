aws-alfred-workflow
===================

AWS workflow for Alfred 3.

This workflow allows you to search through various AWS resources by ID, name and/or tag.

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
Select the AWS profile to use by opening Alfred and typing:

`aws >profile <profile name>`


## Searching
Open Alfred and type:

`aws <query>`

To perform a query against your selected profile. Alfred will then auto-populate results that are visible in your AWS account.


#### Modifier Key Cheat Sheet
Below is a table describing the currently supported AWS resource lookups and what Alfred will do upon hitting **Enter** when combined with modifier keys:

|                                                             | (none)                      | Cmd                                             | Alt / Option | Ctrl | Shift <sub>(_press_, not hold)</sub> |
| :---:                                                       | ---                         | ---                                             | ---        | ---  | ---                                  |
| ![](icons/cfn_stack.png)CloudFormation                      | Open stack in AWS console   |                                                 |            |      | Quicklook                            |
| ![](icons/ec2_instance.png)<br/>EC2                         | Copies _private_ IP         | Open instance in AWS console                    | Copies _public_ IP (if available) |      | Quicklook                            |
| ![](icons/services/lambda.png)<br/>Lambda                   | Open lambda in AWS console  |                                                 |            |      | Quicklook                            |
| ![](icons/db_instance.png)![](icons/db_cluster.png)<br/>RDS | Copy endpoint URL           | Open cluster or node in AWS Console             |                                          |      | Quicklook                            |
| ![](icons/services/redshift.png)<br/>Redshift               | Open cluster in AWS console | Copies first node's _private_ IP (if available) | Copies first node's _public_ IP (if available)    |      | Quicklook                            |
| ![](icons/s3_bucket.png)<br/>S3                             | Open bucket in AWS Console  |                                                 |            |      | Quicklook                            |
| ![](icons/sqs_queue.png)<br/>SQS                            | Open queue in AWS console   | Copy queue URL                                  |                         |      | Quicklook                            |

... more resources and modifiers to be implemented. Feel free to [fork this repo](#fork-destination-box) to implement your own!


## Advanced
### Facets

Search queries can be in the form of a space separated list of `facet:value` or
simply just `value`.  Single (`'`) or double (`"`) quotes may be used for either
the `facet` or `value` to allow for spaces,  and escapes (`\\`) can be used to
escape a literal apostrophe or quotation character.  Furthermore, colons in
`facets` and `values` can be specified by quoting the string (e.g.:
`url:'www.august8.net:8080'`).

The available `facets` for each service, as well as the default `facet` if not provided, is specified for each service below.

#### EC2 Facets

If a bare `value` starts with `i-`, the workflow will search for exact prefix matches against the EC2 Instance Id.  Otherwise, bare `value` queries will search the `Name` tag for the instance.

All other facets map to the tags on the instance.  Note, all tag names are
converted to lowercase.

#### S3 Facets

The default facet is the `Name` tag for the bucket.

All other facets map to the tags on the bucket.  Note, all tag names are converted to lowercase.

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
See [Releases](https://github.com/twang817/aws-alfred-workflow/releases) for a detailed list of changes between versions

Contributors
============
* [rkoval](https://github.com/rkoval)
