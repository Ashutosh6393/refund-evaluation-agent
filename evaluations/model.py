from typing import Dict, List, Optional, cast

from deepeval.models import GrokModel
from deepeval.models.llms.multimodal import reject_audio
from deepeval.test_case import Audio


class XaiJudge(GrokModel):
    """Judge model that talks to xAI.

    DeepEval turns the prompt into an OpenAI-style list of content parts and
    passes that list to ``xai_sdk.chat.user``. That helper expects a string
    (or one content part per argument), so the list lands in the protobuf
    message and raises TypeError. Text prompts are sent as a string instead.
    """

    def _prompt_content(
        self, prompt: str, audio: Optional[List[Audio]] = None
    ) -> List[Dict]:
        reject_audio(audio, "GrokModel")
        return cast(List[Dict], prompt)


eval_model = XaiJudge(model="grok-4.3")
