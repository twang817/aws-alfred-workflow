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

Usage
=====

Select the AWS profile to use via:

`awsprofile <profile name>`

Now, you can search your EC2 instances via:

`aws <query>`

* Select an instance to copy the private IP address to your clipboard.
* Hold `SHIFT` to copy public IP address to your clipboard.
* Hold `CMD` to open AWS web console to that instance.
