from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Literal


app = FastAPI()

class SvmQueryParams(BaseModel):
    # --- Basic Filters ---
    name: Optional[str] = Field(None, description="Filter by name")
    uuid: Optional[str] = Field(None, description="Filter by uuid")
    state: Optional[str] = Field(None, description="Filter by state")
    subtype: Optional[str] = Field(None, description="Filter by subtype")
    comment: Optional[str] = Field(None, description="Filter by comment")
    language: Optional[str] = Field(None, description="Filter by language")

    # --- NIS ---
    # serialization_alias is the MAGIC key. 
    # It tells Pydantic: "When converting to dict/json, use this name."
    nis_enabled: Optional[bool] = Field(None, serialization_alias="nis.enabled")
    nis_servers: Optional[str] = Field(None, serialization_alias="nis.servers")
    nis_domain: Optional[str] = Field(None, serialization_alias="nis.domain")

    # --- DNS ---
    dns_servers: Optional[str] = Field(None, serialization_alias="dns.servers")
    dns_domains: Optional[str] = Field(None, serialization_alias="dns.domains")

    # --- IPSpace ---
    ipspace_name: Optional[str] = Field(None, serialization_alias="ipspace.name")
    ipspace_uuid: Optional[str] = Field(None, serialization_alias="ipspace.uuid")

    # --- Protocols ---
    nfs_allowed: Optional[bool] = Field(None, serialization_alias="nfs.allowed")
    cifs_allowed: Optional[bool] = Field(None, serialization_alias="cifs.allowed")
    iscsi_allowed: Optional[bool] = Field(None, serialization_alias="iscsi.allowed")
    nvme_allowed: Optional[bool] = Field(None, serialization_alias="nvme.allowed")
    fcp_allowed: Optional[bool] = Field(None, serialization_alias="fcp.allowed")

    # --- Storage ---
    storage_allocated: Optional[int] = Field(None, serialization_alias="storage.allocated")
    storage_available: Optional[int] = Field(None, serialization_alias="storage.available")
    storage_used_pct: Optional[int] = Field(None, serialization_alias="storage.used_percentage")

    # --- API Controls ---
    fields: Optional[List[str]] = Field(None)
    max_records: Optional[int] = Field(None)
    order_by: Optional[List[str]] = Field(None)

    # This replaces your custom to_dict() method
    def to_api_params(self):
        # by_alias=True tells Pydantic to use the 'serialization_alias' names
        # exclude_none=True removes keys with None values (cleaning the output)
        return self.model_dump(by_alias=True, exclude_none=True)
    
    
class SvmIpSpace(BaseModel):
    name: Optional[str] = Field("Default", description="IPSpace Name")
    uuid: Optional[str] = None

class SvmDns(BaseModel):
    servers: List[str]
    domains: List[str]

class SvmNis(BaseModel):
    servers: List[str]
    domain: str

class SvmLdap(BaseModel):
    servers: Optional[List[str]] = None
    ad_domain: Optional[str] = None
    bind_dn: str
    base_dn: str

class SvmCifsAdDomain(BaseModel):
    fqdn: str
    user: str
    password: str

class SvmCifs(BaseModel):
    name: str
    ad_domain: SvmCifsAdDomain

class SvmRoute(BaseModel):
    gateway: str
    destination: Optional[str] = "0.0.0.0/0"

class SvmIpInterface(BaseModel):
    name: str
    ip_address: str = Field(alias="ip.address") # Example of handling nested input mapping if needed
    netmask: str = Field(alias="ip.netmask")
    # You can expand this model to include location/home_port as needed

class SvmS3Certificate(BaseModel):
    name: Optional[str] = None
    uuid: Optional[str] = None

class SvmS3(BaseModel):
    name: Optional[str] = "_S3Server"
    enabled: bool = True
    port: Optional[int] = 80
    secure_port: Optional[int] = 443
    is_http_enabled: bool = True
    is_https_enabled: bool = False
    certificate: Optional[SvmS3Certificate] = None

# base Model schema to create svm
class SvmCreateRequest(BaseModel):
    # Required
    name: str = Field(..., description="Name of the SVM")

    # Recommended / Optional
    ipspace: Optional[SvmIpSpace] = Field(default_factory=SvmIpSpace)
    language: Optional[str] = "C.UTF-8"
    subtype: Optional[str] = "default"
    snapshot_policy: Optional[str] = Field(None, alias="snapshot_policy.name")
    anti_ransomware_default_volume_state: Optional[str] = "disabled"
    qos_adaptive_policy_group_template: Optional[str] = None

    # Complex Nested Objects
    dns: Optional[SvmDns] = None
    nis: Optional[SvmNis] = None
    ldap: Optional[SvmLdap] = None
    cifs: Optional[SvmCifs] = None
    s3: Optional[SvmS3] = None
    
    routes: Optional[List[SvmRoute]] = None
    ip_interfaces: Optional[List[SvmIpInterface]] = None

    # Storage Settings
    storage_limit: Optional[int] = Field(None, alias="storage.limit")
    storage_alert_threshold: Optional[int] = Field(None, alias="storage.limit_threshold_alert")

    # --- THE VALIDATION LOGIC ---
    @model_validator(mode='after')
    def check_cifs_requirements(self):
        """
        Enforce Rule: If CIFS is provided, interfaces, routes and DNS must be provided.
        """
        if self.cifs is not None:
            errors = []
            if not self.dns:
                errors.append("DNS configuration is required when CIFS is enabled.")
            if not self.ip_interfaces:
                errors.append("IP Interfaces are required when CIFS is enabled.")
            if not self.routes:
                errors.append("Routes are required when CIFS is enabled.")
            
            if errors:
                raise ValueError(f"CIFS Dependency Error: {', '.join(errors)}")
        return self

    # --- PAYLOAD BUILDER ---
    def to_netapp_payload(self) -> dict:
        """
        Converts this Pydantic model into the nested dictionary 
        structure the NetApp API expects.
        """
        # Start with a basic dump
        set_fields = self.model_fields_set
        payload = {
            "name": self.name,

        }
        if "language" in set_fields:
            payload["language"] = self.language
        if "subtype" in set_fields:
            payload["subtype"]= self.subtype
            
        if "ipspace" in set_fields and self.ipspace and self.ipspace.name:
            ipspace_fields = self.ipspace.model_fields_set
            ipspace_data = {}

            if "uuid" in ipspace_fields:
                ipspace_data["uuid"] = self.ipspace.uuid
                # Optional: If the user explicitly provided BOTH uuid and name, send both.
                # But we skip the 'Default' name if it was auto-generated.
                if "name" in ipspace_fields:
                    ipspace_data["name"] = self.ipspace.name
            elif "name" in ipspace_fields:
                # User provided a custom name (e.g., "ipspace_A") but no UUID
                ipspace_data["name"] = self.ipspace.name
            
            else:
                # Case: User sent "ipspace": {} 
                # They want the ipspace config, but didn't type anything.
                # We send the default value "Default".
                ipspace_data["name"] = self.ipspace.name

            payload["ipspace"] = ipspace_data

        if "snapshot_policy" in set_fields and self.snapshot_policy:
                payload["snapshot_policy"] = {"name": self.snapshot_policy}
        
        if "anti_ransomware_default_volume_state" in set_fields:
            payload["anti_ransomware_default_volume_state"] = self.anti_ransomware_default_volume_state

        # Add generic nested objects if they exist
        if self.dns:
            payload["dns"] = self.dns.model_dump()
        
        if self.nis:
            payload["nis"] = self.nis.model_dump()

        if self.ldap:
            payload["ldap"] = self.ldap.model_dump(exclude_none=True)

        if self.cifs:
            payload["cifs"] = {
                "name": self.cifs.name,
                "ad_domain": {
                    "fqdn": self.cifs.ad_domain.fqdn,
                    "user": self.cifs.ad_domain.user,
                    "password": self.cifs.ad_domain.password
                }
            }

        # Handle S3 specifics and defaults
        if self.s3:
            s3_data = self.s3.model_dump(exclude_none=True)
            # If S3 is enabled but no name provided, ensures default matches prompt logic
            if not s3_data.get("name"):
                s3_data["name"] = "_S3Server"
            payload["s3"] = s3_data

        # Clean up None values to avoid sending empty keys
        return {k: v for k, v in payload.items() if v is not None}
