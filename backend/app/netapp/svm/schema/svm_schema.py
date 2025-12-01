from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Literal


app = FastAPI()


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
    # qos_adaptive_policy_group_template: Optional[str] = Field(None, alias="qos.adaptive_policy_group_template")

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
        payload = {
            "name": self.name,
            "language": self.language,
            "subtype": self.subtype,
            "ipspace": {"name": self.ipspace.name} if self.ipspace and self.ipspace.name else None,
            "snapshot_policy": {"name": self.snapshot_policy} if self.snapshot_policy else None,
            "anti_ransomware_default_volume_state": self.anti_ransomware_default_volume_state

        }

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
