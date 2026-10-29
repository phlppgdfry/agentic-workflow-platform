from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Principal(StrictModel):
    subject: str = Field(min_length=1, max_length=80)
    tenant: str = Field(min_length=1, max_length=80)
    roles: list[Literal["builder", "operator", "approver", "auditor"]] = Field(min_length=1)


class RunRequest(StrictModel):
    customer_id: str = Field(pattern=r"^C-[0-9]{3}$")
    message: str = Field(min_length=1, max_length=4000)


class LookupArgs(StrictModel):
    customer_id: str = Field(pattern=r"^C-[0-9]{3}$")


class PolicyArgs(StrictModel):
    topic: Literal["accounting_intake"]


class PrepareArgs(StrictModel):
    customer_id: str = Field(pattern=r"^C-[0-9]{3}$")
    title: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1, max_length=1200)
    priority: Literal["normal", "high"]


class LookupCall(StrictModel):
    tool: Literal["lookup_customer"]
    arguments: LookupArgs


class PolicyCall(StrictModel):
    tool: Literal["check_policy"]
    arguments: PolicyArgs


class PrepareCall(StrictModel):
    tool: Literal["prepare_case"]
    arguments: PrepareArgs


ToolCall = Annotated[LookupCall | PolicyCall | PrepareCall, Field(discriminator="tool")]


class Plan(StrictModel):
    steps: list[ToolCall] = Field(min_length=3, max_length=3)

    def check_scope(self, customer_id: str) -> None:
        if [s.tool for s in self.steps] != ["lookup_customer", "check_policy", "prepare_case"]:
            raise ValueError("Plan must look up customer, check policy, then prepare a case")
        if any(getattr(s.arguments, "customer_id", customer_id) != customer_id for s in self.steps):
            raise ValueError("Plan tried to change customer scope")


class Decision(StrictModel):
    approve: bool = Field(strict=True)
    reason: str = Field(min_length=5, max_length=500)
