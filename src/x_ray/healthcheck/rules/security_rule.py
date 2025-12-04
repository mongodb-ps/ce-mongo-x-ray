from x_ray.healthcheck.rules.base_rule import BaseRule
from x_ray.healthcheck.issues import ISSUE, create_issue


class SecurityRule(BaseRule):
    def apply(self, data: object, **kwargs) -> tuple:
        """Check the security settings for any issues.

        Args:
            data (object): The getCmdLineOpts data.
            extra_info (dict, optional): Extra information such as host. Defaults to None.
        Returns:
            tuple: (list of issues found, list of parsed data)
        """
        host = kwargs.get("extra_info", {}).get("host", "unknown")
        test_result = []
        parsed = data.get("parsed", {})
        security_settings = parsed.get("security", {})
        net = parsed.get("net", {})
        audit_log = parsed.get("auditLog", {})
        authorization = security_settings.get("authorization", None)
        redact_logs = security_settings.get("redactClientLogData", None)
        bind_ip = net.get("bindIp", "127.0.0.1")
        port = net.get("port", None)
        tls_enabled = net.get("tls", {}).get("mode", None)
        audit = "enabled" if audit_log.get("destination", None) is not None else "disabled"
        ear_enabled = security_settings.get("enableEncryption", False)
        ear_keyfile = security_settings.get("encryptionKeyFile", None)
        if authorization != "enabled":
            issue = create_issue(ISSUE.AUTHORIZATION_DISABLED, host=host)
            test_result.append(issue)
        if not redact_logs:
            issue = create_issue(ISSUE.LOG_REDACTION_DISABLED, host=host)
            test_result.append(issue)
        if tls_enabled is None:
            issue = create_issue(ISSUE.TLS_DISABLED, host=host)
            test_result.append(issue)
        elif tls_enabled != "requireTLS":
            issue = create_issue(ISSUE.OPTIONAL_TLS, host=host, params={"tls_mode": tls_enabled})
            test_result.append(issue)
        if bind_ip == "0.0.0.0":
            issue = create_issue(ISSUE.OPEN_BIND_IP, host=host)
            test_result.append(issue)
        if port == 27017:
            issue = create_issue(ISSUE.DEFAULT_PORT_USED, host=host)
            test_result.append(issue)
        if audit == "disabled":
            issue = create_issue(ISSUE.AUDITING_DISABLED, host=host)
            test_result.append(issue)
        if not ear_enabled:
            issue = create_issue(ISSUE.ENCRYPTION_AT_REST_DISABLED, host=host)
            test_result.append(issue)
        if ear_keyfile is not None:
            issue = create_issue(ISSUE.ENCRYPTION_AT_REST_USING_KEYFILE, host=host)
            test_result.append(issue)

        return test_result, data
