from fastapi import Query, Depends, HTTPException
from typing import Optional, List

class SvmQueryParams:
    def __init__(
        self,
        # --- Basic Filters ---
        name: Optional[str] = Query(None, description="Filter by name"),
        uuid: Optional[str] = Query(None, description="Filter by uuid"),
        state: Optional[str] = Query(None, description="Filter by state"),
        subtype: Optional[str] = Query(None, description="Filter by subtype"),
        comment: Optional[str] = Query(None, description="Filter by comment"),
        language: Optional[str] = Query(None, description="Filter by language"),
        
        # --- NIS ---
        nis_enabled: Optional[bool] = Query(None, alias="nis.enabled"),
        nis_servers: Optional[str] = Query(None, alias="nis.servers"),
        nis_domain: Optional[str] = Query(None, alias="nis.domain"),
        
        # --- DNS ---
        dns_servers: Optional[str] = Query(None, alias="dns.servers"),
        dns_domains: Optional[str] = Query(None, alias="dns.domains"),
        
        # --- LDAP ---
        ldap_enabled: Optional[bool] = Query(None, alias="ldap.enabled"),
        ldap_base_dn: Optional[str] = Query(None, alias="ldap.base_dn"),
        ldap_servers: Optional[str] = Query(None, alias="ldap.servers"),
        ldap_bind_dn: Optional[str] = Query(None, alias="ldap.bind_dn"),
        ldap_ad_domain: Optional[str] = Query(None, alias="ldap.ad_domain"),

        # --- IPSpace ---
        ipspace_name: Optional[str] = Query(None, alias="ipspace.name"),
        ipspace_uuid: Optional[str] = Query(None, alias="ipspace.uuid"),

        # --- Aggregates ---
        aggregates_name: Optional[str] = Query(None, alias="aggregates.name"),
        aggregates_uuid: Optional[str] = Query(None, alias="aggregates.uuid"),

        # --- Protocols (Allowed/Enabled) ---
        nfs_allowed: Optional[bool] = Query(None, alias="nfs.allowed"),
        nfs_enabled: Optional[bool] = Query(None, alias="nfs.enabled"),
        cifs_allowed: Optional[bool] = Query(None, alias="cifs.allowed"),
        cifs_enabled: Optional[bool] = Query(None, alias="cifs.enabled"),
        iscsi_allowed: Optional[bool] = Query(None, alias="iscsi.allowed"),
        iscsi_enabled: Optional[bool] = Query(None, alias="iscsi.enabled"),
        nvme_allowed: Optional[bool] = Query(None, alias="nvme.allowed"),
        nvme_enabled: Optional[bool] = Query(None, alias="nvme.enabled"),
        fcp_allowed: Optional[bool] = Query(None, alias="fcp.allowed"),
        fcp_enabled: Optional[bool] = Query(None, alias="fcp.enabled"),
        ndmp_allowed: Optional[bool] = Query(None, alias="ndmp.allowed"),

        # --- S3 ---
        s3_name: Optional[str] = Query(None, alias="s3.name"),
        s3_allowed: Optional[bool] = Query(None, alias="s3.allowed"),
        s3_enabled: Optional[bool] = Query(None, alias="s3.enabled"),
        s3_is_http_enabled: Optional[bool] = Query(None, alias="s3.is_http_enabled"),
        s3_is_https_enabled: Optional[bool] = Query(None, alias="s3.is_https_enabled"),
        s3_port: Optional[int] = Query(None, alias="s3.port"),
        s3_secure_port: Optional[int] = Query(None, alias="s3.secure_port"),
        s3_cert_uuid: Optional[str] = Query(None, alias="s3.certificate.uuid"),
        s3_cert_name: Optional[str] = Query(None, alias="s3.certificate.name"),

        # --- CIFS Specifics ---
        cifs_name: Optional[str] = Query(None, alias="cifs.name"),
        cifs_ad_fqdn: Optional[str] = Query(None, alias="cifs.ad_domain.fqdn"),
        cifs_ad_ou: Optional[str] = Query(None, alias="cifs.ad_domain.organizational_unit"),

        # --- NSSwitch ---
        nsswitch_netgroup: Optional[str] = Query(None, alias="nsswitch.netgroup"),
        nsswitch_group: Optional[str] = Query(None, alias="nsswitch.group"),
        nsswitch_hosts: Optional[str] = Query(None, alias="nsswitch.hosts"),
        nsswitch_namemap: Optional[str] = Query(None, alias="nsswitch.namemap"),
        nsswitch_passwd: Optional[str] = Query(None, alias="nsswitch.passwd"),

        # --- QoS & Anti-Ransomware ---
        qos_policy_name: Optional[str] = Query(None, alias="qos_policy.name"),
        qos_policy_uuid: Optional[str] = Query(None, alias="qos_policy.uuid"),
        ar_default_vol_state: Optional[str] = Query(None, alias="anti_ransomware_default_volume_state"),
        
        # --- Storage & Usage ---
        max_volumes: Optional[str] = Query(None, alias="max_volumes"),
        storage_allocated: Optional[int] = Query(None, alias="storage.allocated"),
        storage_available: Optional[int] = Query(None, alias="storage.available"),
        storage_used_pct: Optional[int] = Query(None, alias="storage.used_percentage"),
        storage_limit: Optional[int] = Query(None, alias="storage.limit"),
        
        # --- API Controls ---
        fields: Optional[List[str]] = Query(None, description="Specify fields to return"),
        max_records: Optional[int] = Query(None, description="Limit records"),
        return_records: bool = Query(True, description="Default true for GET"),
        return_timeout: int = Query(15, ge=0, le=120, description="Timeout in seconds"),
        order_by: Optional[List[str]] = Query(None, description="Order results")
    ):
        # We capture all local variables into a dictionary
        self.params = {k: v for k, v in locals().items() if k != 'self' and v is not None}

        # Handling Aliases manually for the dictionary logic because 'locals()' gives 
        # the python variable name (e.g., nis_enabled), but we need 'nis.enabled'.
        # The clean way is to map them or trust the API client. 
        # However, FastAPI's 'Query(alias=...)' only helps parsing incoming requests.
        # We need to reconstruct the dots for the OUTGOING request to NetApp.
        
        self.api_params = {}
        
        # Helper to map python_var to netapp.var
        mapping = {
            "nis_enabled": "nis.enabled",
            "nis_servers": "nis.servers",
            "nis_domain": "nis.domain",
            "dns_servers": "dns.servers",
            "dns_domains": "dns.domains",
            "ldap_enabled": "ldap.enabled",
            "ldap_base_dn": "ldap.base_dn",
            "ldap_servers": "ldap.servers",
            "ldap_bind_dn": "ldap.bind_dn",
            "ldap_ad_domain": "ldap.ad_domain",
            "ipspace_name": "ipspace.name",
            "ipspace_uuid": "ipspace.uuid",
            "aggregates_name": "aggregates.name",
            "aggregates_uuid": "aggregates.uuid",
            "nfs_allowed": "nfs.allowed",
            "nfs_enabled": "nfs.enabled",
            "cifs_allowed": "cifs.allowed",
            "cifs_enabled": "cifs.enabled",
            "iscsi_allowed": "iscsi.allowed",
            "iscsi_enabled": "iscsi.enabled",
            "nvme_allowed": "nvme.allowed",
            "nvme_enabled": "nvme.enabled",
            "fcp_allowed": "fcp.allowed",
            "fcp_enabled": "fcp.enabled",
            "ndmp_allowed": "ndmp.allowed",
            "s3_name": "s3.name",
            "s3_allowed": "s3.allowed",
            "s3_enabled": "s3.enabled",
            "s3_is_http_enabled": "s3.is_http_enabled",
            "s3_is_https_enabled": "s3.is_https_enabled",
            "s3_port": "s3.port",
            "s3_secure_port": "s3.secure_port",
            "s3_cert_uuid": "s3.certificate.uuid",
            "s3_cert_name": "s3.certificate.name",
            "cifs_name": "cifs.name",
            "cifs_ad_fqdn": "cifs.ad_domain.fqdn",
            "cifs_ad_ou": "cifs.ad_domain.organizational_unit",
            "nsswitch_netgroup": "nsswitch.netgroup",
            "nsswitch_group": "nsswitch.group",
            "nsswitch_hosts": "nsswitch.hosts",
            "nsswitch_namemap": "nsswitch.namemap",
            "nsswitch_passwd": "nsswitch.passwd",
            "qos_policy_name": "qos_policy.name",
            "qos_policy_uuid": "qos_policy.uuid",
            "ar_default_vol_state": "anti_ransomware_default_volume_state",
            "storage_allocated": "storage.allocated",
            "storage_available": "storage.available",
            "storage_used_pct": "storage.used_percentage",
            "storage_limit": "storage.limit",
        }

        for py_name, value in self.params.items():
            # If there is a mapped name (dot notation), use it. Otherwise use the variable name.
            api_key = mapping.get(py_name, py_name)
            self.api_params[api_key] = value

    def to_dict(self):
        return self.api_params