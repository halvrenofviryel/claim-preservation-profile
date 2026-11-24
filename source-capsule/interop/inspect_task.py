"""Deterministic Inspect AI task for a format-compatibility probe."""

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.model import (
    ChatMessage,
    GenerateConfig,
    ModelAPI,
    ModelOutput,
    ModelUsage,
    modelapi,
)
from inspect_ai.scorer import exact
from inspect_ai.solver import generate
from inspect_ai.tool import ToolChoice, ToolInfo


@modelapi(name="claim-commons-local")
class DeterministicLocalModel(ModelAPI):
    async def generate(
        self,
        input: list[ChatMessage],
        tools: list[ToolInfo],
        tool_choice: ToolChoice,
        config: GenerateConfig,
    ) -> ModelOutput:
        output = ModelOutput.from_content(
            model=f"claim-commons-local/{self.model_name}",
            content="local deterministic answer",
        )
        output.usage = ModelUsage(input_tokens=3, output_tokens=3, total_tokens=6)
        return output


@task
def claim_commons_compatibility_probe():
    return Task(
        dataset=[
            Sample(
                input=f"Synthetic local export case {index}",
                target=(
                    "local deterministic answer"
                    if index < 4
                    else "intentionally different expected answer"
                ),
            )
            for index in range(1, 5)
        ],
        solver=[generate()],
        scorer=exact(),
        model="claim-commons-local/synthetic-echo-v1",
    )
