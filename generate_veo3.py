#!/usr/bin/env python3

import json
import os
import time
from typing import Optional
import requests
import utils


# BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
# API_KEY = "<YOUR_API_KEY>"

BASE_URL = "https://api.thucchien.ai/v1beta"
API_KEY = "<YOUR_API_KEY>"


MODEL = "veo-3.1-generate-preview:predictLongRunning"


PROMPT = """A reverent and respectful scene of people lining up to offer incense (Dâng hương) at the memorial site.
The atmosphere is solemn and quiet, focusing on flowers and offerings. Warm, soft lighting, 16:9, documentary style.
Professional Vietnamese female news anchor MC speaks in background: "Các hoạt động dâng hương tại khu di tích các anh hùng liệt sỹ tại Quảng Trị đã thể hiện lòng biết ơn sâu sắc của toàn dân với các anh hùng liệt sỹ đã hy sinh vì độc lập tự do của Tổ quốc..."
"""

IMAGE = 'ref/thoisu.jpg'

REFERENCE_IMAGES = [
    # "ref/dieubinh.jpg",
    "ref/thoisu.jpg",
]


class VeoVideoGenerator:
    """Complete Veo video generation client using LiteLLM proxy."""

    def __init__(
        self,
        base_url: str = BASE_URL,
        api_key: str = "sk-1234",
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

    def generate_video(self, prompt: str) -> Optional[str]:
        print(f"🎬 Generating video with prompt: '{prompt}'")

        url = f"{self.base_url}/models/{MODEL}"
        payload = {
            "instances": [
                {
                    "prompt": prompt,
                    # "image": {
                    #     # Union field can be only one of the following:
                    #     "bytesBase64Encoded": utils.image_to_base64(IMAGE),
                    #     # "gcsUri": 'string',
                    #     # End of list of possible types for union field.
                    #     "mimeType": 'image/jpg'
                    # },
                    # "lastFrame": {
                    #     # Union field can be only one of the following:
                    #     "bytesBase64Encoded": 'string',
                    #     "gcsUri": 'string',
                    #     # End of list of possible types for union field.
                    #     "mimeType": 'string'
                    # },
                    # "video": {
                    #     # Union field can be only one of the following:
                    #     "bytesBase64Encoded": 'string',
                    #     "gcsUri": 'string',
                    #     # End of list of possible types for union field.
                    #     "mimeType": 'string'
                    # },
                    # "mask": {
                    #     # Union field can be only one of the following:
                    #     "bytesBase64Encoded": 'string',
                    #     "gcsUri": 'string',
                    #     # End of list of possible types for union field.
                    #     "mimeType": 'string',
                    #     "maskMode": 'string'
                    # },
                }
            ],
            "parameters": {
                "aspectRatio": '16:9',
                # "compressionQuality": 'optimized',
                # "durationSeconds": 8,
                # "enhancePrompt": True,
                # "generateAudio": True,
                # "negativePrompt": "...",
                # "personGeneration": 'allow_adult',
                # "resizeMode": 'pad', # Veo 3 image-to-video only
                # "resolution": "1080p", # Veo 3 models only
                # "sampleCount": 1,
                # "seed": 12345,
                # "storageUri": ""
            }
        }
        if REFERENCE_IMAGES:
            ref = []
            for img in REFERENCE_IMAGES:
                print(f"🖼️  Using reference image: {img}")
                base64_img = utils.image_to_base64(img)
                ref.append(
                    {
                        "image": {
                            "bytesBase64Encoded": base64_img,
                            "mimeType": "image/jpeg",
                        },
                        # "referenceType": "asset",
                    }
                )
            payload["instances"][0]["referenceImages"] = ref
        
        print(f"Payload: {json.dumps(payload, indent=2)[:500]}")

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()

            data = response.json()
            operation_name = data.get("name")

            if operation_name:
                print(f"✅ Video generation started: {operation_name}")
                return operation_name
            else:
                print("❌ No operation name returned")
                print(f"Response: {json.dumps(data, indent=2)}")
                return None

        except requests.RequestException as e:
            print(f"❌ Failed to start video generation: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"Error details: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Error response: {e.response.text}")
            return None

    def wait_for_completion(
        self, operation_name: str, max_wait_time: int = 600
    ) -> Optional[str]:
        print("⏳ Waiting for video generation to complete...")

        operation_url = f"{self.base_url}/{operation_name}"
        start_time = time.time()
        poll_interval = 10  # Start with 10 seconds

        while time.time() - start_time < max_wait_time:
            try:
                print(
                    f"🔍 Polling status... ({int(time.time() - start_time)}s elapsed)"
                )

                response = requests.get(operation_url, headers=self.headers)
                response.raise_for_status()

                data = response.json()

                # Check for errors
                if "error" in data:
                    print("❌ Error in video generation:")
                    print(json.dumps(data["error"], indent=2))
                    return None

                # Check if operation is complete
                is_done = data.get("done", False)

                if is_done:
                    print("🎉 Video generation complete!")

                    try:
                        # Extract video URI from nested response
                        video_uri = data["response"]["generateVideoResponse"][
                            "generatedSamples"
                        ][0]["video"]["uri"]
                        print(f"📹 Video URI: {video_uri}")
                        return video_uri
                    except KeyError as e:
                        print(f"❌ Could not extract video URI: {e}")
                        print("Full response:")
                        print(json.dumps(data, indent=2))
                        return None

                # Wait before next poll, with exponential backoff
                time.sleep(poll_interval)
                poll_interval = min(poll_interval * 1.2, 30)  # Cap at 30 seconds

            except requests.RequestException as e:
                print(f"❌ Error polling operation status: {e}")
                time.sleep(poll_interval)

        print(f"⏰ Timeout after {max_wait_time} seconds")
        return None

    def download_video(
        self, video_uri: str, output_filename: str = "generated_video.mp4"
    ) -> bool:
        """
        Download the generated video file.

        Args:
            video_uri: URI of the video to download (from Google's response)
            output_filename: Local filename to save the video

        Returns:
            True if download successful, False otherwise
        """
        print(f"⬇️  Downloading video...")
        print(f"Original URI: {video_uri}")

        # Convert Google URI to LiteLLM proxy URI
        # Example: https://generativelanguage.googleapis.com/v1beta/files/abc123 -> /gemini/download/v1beta/files/abc123:download?alt=media
        if video_uri.startswith("https://generativelanguage.googleapis.com/"):
            relative_path = video_uri.replace(
                "https://generativelanguage.googleapis.com/", ""
            )
        else:
            relative_path = video_uri

        # base_url: https://api.thucchien.ai/gemini/v1beta
        if self.base_url.endswith("/v1beta"):
            base_path = self.base_url.replace("/v1beta", "/download")
        else:
            base_path = self.base_url

        litellm_download_url = f"{base_path}/{relative_path}"
        print(f"Download URL: {litellm_download_url}")

        try:
            # Download with streaming and redirect handling
            response = requests.get(
                litellm_download_url,
                headers=self.headers,
                stream=True,
                allow_redirects=True,  # Handle redirects automatically
            )
            response.raise_for_status()

            # Save video file
            with open(output_filename, "wb") as f:
                downloaded_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # Progress indicator for large files
                        if downloaded_size % (1024 * 1024) == 0:  # Every MB
                            print(
                                f"📦 Downloaded {downloaded_size / (1024*1024):.1f} MB..."
                            )

            # Verify file was created and has content
            if os.path.exists(output_filename):
                file_size = os.path.getsize(output_filename)
                if file_size > 0:
                    print(f"✅ Video downloaded successfully!")
                    print(f"📁 Saved as: {output_filename}")
                    print(f"📏 File size: {file_size / (1024*1024):.2f} MB")
                    return True
                else:
                    print("❌ Downloaded file is empty")
                    os.remove(output_filename)
                    return False
            else:
                print("❌ File was not created")
                return False

        except requests.RequestException as e:
            print(f"❌ Download failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                print(f"Response headers: {dict(e.response.headers)}")
            return False

    def generate_and_download(self, prompt: str, output_filename: str = None) -> bool:
        # Auto-generate filename if not provided
        if output_filename is None:
            timestamp = int(time.time())
            safe_prompt = "".join(
                c for c in prompt[:30] if c.isalnum() or c in (" ", "-", "_")
            ).rstrip()
            output_filename = (
                f"result/veo_video_{safe_prompt.replace(' ', '_')}_{timestamp}.mp4"
            )

        print("=" * 60)
        print("🎬 VEO VIDEO GENERATION WORKFLOW")
        print("=" * 60)

        # Step 1: Generate video
        operation_name = self.generate_video(PROMPT)
        if not operation_name:
            return False

        # Step 2: Wait for completion
        video_uri = self.wait_for_completion(operation_name)
        if not video_uri:
            return False

        # Step 3: Download video
        success = self.download_video(video_uri, output_filename)

        if success:
            print("=" * 60)
            print("🎉 SUCCESS! Video generation complete!")
            print(f"📁 Video saved as: {output_filename}")
            print("=" * 60)
        else:
            print("=" * 60)
            print("❌ FAILED! Video generation or download failed")
            print("=" * 60)

        return success


def main():
    # Configuration from environment or defaults
    base_url = os.getenv("LITELLM_BASE_URL", BASE_URL)
    api_key = os.getenv("LITELLM_API_KEY", API_KEY)

    print("🚀 Starting Veo Video Generation Example")
    print(f"📡 Using LiteLLM proxy at: {base_url}")

    # Initialize generator
    generator = VeoVideoGenerator(base_url=base_url, api_key=api_key)

    print(f"🎬 Using prompt: '{PROMPT}'")

    # Generate and download video
    success = generator.generate_and_download(PROMPT)

    if success:
        print("✅ Example completed successfully!")
    else:
        print("❌ Example failed!")
        print("🔧 Check your API Configuration")


if __name__ == "__main__":
    main()
