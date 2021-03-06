#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
scf
~~~~~~~~~~~~~~
This module implements scf api
"""

import os
import json
from tencentserverless.exception import TencentServerlessSDKException
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.scf.v20180416 import scf_client
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.profile.client_profile import ClientProfile


class Client(object):
    """
    Client
    ~~~~~~~~~~~~~~
    This class default a client for scf api
    """

    def __init__(self,
                 region=None,
                 secret_id=None,
                 secret_key=None,
                 token=None):

        self.region = region

        self.secret_id = secret_id

        self.secret_key = secret_key

        self.token = token

    def invoke(self, function_name,
               namespace="default",
               log_type="None",
               qualifier="$LATEST",
               invocation_type="RequestResponse",
               data=None):

        self.region = self.region if self.region is not None \
            else os.environ.get("TENCENTCLOUD_REGION", "ap-guangzhou")

        self.secret_id = self.secret_id if self.secret_id is not None \
            else os.environ.get("TENCENTCLOUD_SECRETID", None)

        self.secret_key = self.secret_key if self.secret_key is not None \
            else os.environ.get("TENCENTCLOUD_SECRETKEY", None)

        self.token = self.token if self.token is not None \
            else os.environ.get("TENCENTCLOUD_SESSIONTOKEN", None)

        self.env = os.environ.get("TENCENTCLOUD_RUNENV", None)

        self.endpoint = "scf.internal.tencentcloudapi.com" if self.env == "SCF" \
            else "scf.tencentcloudapi.com"

        cred = credential.Credential(self.secret_id, self.secret_key, self.token)
        self.profile = ClientProfile(httpProfile=HttpProfile(endpoint=self.endpoint, reqTimeout=300, keepAlive=True))
        self.client = scf_client.ScfClient(cred, self.region, profile=self.profile)

        client_context = None
        if data:
            client_context = json.dumps(data)
        action_params = {
            "Namespace": namespace,
            "LogType": log_type,
            "ClientContext": client_context,
            "Qualifier": qualifier,
            "InvocationType": invocation_type,
            "FunctionName": function_name,
        }
        res = json.loads(self.client.call("Invoke", action_params))
        if "Error" in res["Response"]:
            raise TencentCloudSDKException(code=res["Response"]["Error"]["Code"],
                                           message=res["Response"]["Error"]["Message"],
                                           requestId=res["Response"]["RequestId"])
        elif "InvokeResult" in res["Response"]["Result"]:
            if res["Response"]["Result"]["InvokeResult"] == 1:
                exceptions = json.loads(res["Response"]["Result"]["RetMsg"])
                stack_trace = exceptions["stackTrace"] if "stackTrace" in exceptions else ""
                raise TencentServerlessSDKException(code=exceptions["errorCode"],
                                                    message=exceptions["errorMessage"],
                                                    response=res, stack_trace=stack_trace,
                                                    request_id=res["Response"]['RequestId'])
            elif res["Response"]["Result"]["InvokeResult"] == -1:
                raise TencentServerlessSDKException(code=-1,
                                                    message=res["Response"]["Result"]["RetMsg"],
                                                    response=res,
                                                    request_id=res["Response"]['RequestId'])
            else:
                return res["Response"]["Result"]["RetMsg"]
        else:
            raise TencentServerlessSDKException(code=-1, message='Internal server error',
                                                response=res,
                                                request_id=res["Response"]['RequestId'])

    def __getattr__(self, attr_name):
        def wrap(*l, **args):
            log_type = None
            if 'log_type' in args:
                log_type = args['log_type']
                del args['log_type']
            invocation_type = None
            if 'invocation_type' in args:
                invocation_type = args['invocation_type']
                del args['invocation_type']

            qualifier = '$LATEST'
            if 'qualifier' in args:
                qualifier = args['qualifier']
                del args['qualifier']

            namespace = 'default'
            if 'namespace' in args:
                namespace = args['namespace']
                del args['namespace']

            return self.invoke(function_name=attr_name, namespace=namespace,
                               qualifier=qualifier,
                               log_type=log_type,
                               invocation_type=invocation_type, data=args)
        return wrap

    def __getitem__(self, attr_name):
        return self.__getattr__(attr_name)

    def call(self, attr_name):
        return self.__getattr__(attr_name)


def invoke(function_name,
           region=None,
           secret_id=None,
           secret_key=None,
           token=None,
           namespace="default",
           log_type="None",
           qualifier="$LATEST",
           invocation_type="RequestResponse",
           data=None):
    client = Client(region=region, secret_id=secret_id, secret_key=secret_key, token=token)
    return client.invoke(function_name=function_name, namespace=namespace, log_type=log_type,
                         qualifier=qualifier, invocation_type=invocation_type, data=data)