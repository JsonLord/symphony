import logging
from gradio_client import Client, handle_file
import tempfile
import base64
import os

logger = logging.getLogger(__name__)

def convert_image_to_markdown(base64_data: str) -> str:
    """
    Takes a base64 encoded image string (e.g. data:image/png;base64,...),
    saves it to a temporary file, sends it to the Nanonets-OCR2-3B model
    via the Gradio client, and returns the markdown result.
    """
    if not base64_data:
        return ""

    try:
        # Strip the data:image/...;base64, prefix if present
        if "," in base64_data:
            base64_data = base64_data.split(",")[1]

        img_bytes = base64.b64decode(base64_data)

        # Write to a temporary file so handle_file can read it
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(img_bytes)
            tmp_path = tmp.name

        logger.info("Initializing Gradio Client for OCR...")
        client = Client("prithivMLmods/Super-OCRs-Demo")

        logger.info("Sending image to Nanonets-OCR2-3B for markdown conversion...")
        result = client.predict(
            model_choice="Nanonets-OCR2-3B",
            image=handle_file(tmp_path),
            ds_task_type="Convert to Markdown",
            ds_model_size="Large",
            ds_ref_text="Hello!!", # dummy reference text required by API signature
            custom_prompt="Convert to Markdown precisely.",
            max_new_tokens=2048,
            temperature=0.2,
            top_p=0.9,
            top_k=50,
            api_name="/run_model",
        )

        # Cleanup temp file
        try:
            os.remove(tmp_path)
        except:
            pass

        # Result is a tuple where the first element is the markdown string
        if isinstance(result, tuple) and len(result) > 0:
            logger.info("Successfully converted image to markdown.")
            return result[0]
        elif isinstance(result, str):
            return result
        else:
            logger.warning(f"Unexpected result format from OCR API: {result}")
            return str(result)

    except Exception as e:
        logger.error(f"Failed to convert image to markdown via Gradio OCR: {e}")
        return f"\n[Image OCR Failed: {e}]\n"
