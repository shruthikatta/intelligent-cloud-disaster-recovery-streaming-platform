"""Minimal recovery Lambda for StreamVault — invoked by LambdaRecoveryAdapter with JSON body.

Extend this function to call Step Functions, SNS, or Route 53 APIs for real DR automation.
"""

import json


def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({"ok": True, "workflow": event.get("workflow"), "echo": event}),
    }
