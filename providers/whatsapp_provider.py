
# import httpx

# from core.config import settings


# class WhatsAppProvider:

#     @staticmethod
#     def send_otp(phone_number: str, otp: str) -> None:
#         required = [
#             settings.meta_access_token,
#             settings.meta_phone_number_id,
#             settings.meta_graph_api_version,
#             settings.whatsapp_otp_template_name,
#         ]

#         if not all(required):
#             raise RuntimeError(
#                 "WhatsApp Cloud API is not fully configured"
#             )

#         # Store contacts in international format.
#         # Meta's API expects the recipient number without "+".
#         recipient = (
#             phone_number.strip()
#             .replace("+", "")
#             .replace(" ", "")
#             .replace("-", "")
#             .replace("(", "")
#             .replace(")", "")
#         )

#         url = (
#             "https://graph.facebook.com/"
#             f"{settings.meta_graph_api_version}/"
#             f"{settings.meta_phone_number_id}/messages"
#         )

#         payload = {
#             "messaging_product": "whatsapp",
#             "recipient_type": "individual",
#             "to": recipient,
#             "type": "template",
#             "template": {
#                 "name": settings.whatsapp_otp_template_name,
#                 "language": {
#                     "code": settings.whatsapp_otp_language,
#                 },
#                 "components": [
#                     {
#                         "type": "body",
#                         "parameters": [
#                             {
#                                 "type": "text",
#                                 "text": otp,
#                             }
#                         ],
#                     },
#                     {
#                         "type": "button",
#                         "sub_type": "url",
#                         "index": "0",
#                         "parameters": [
#                             {
#                                 "type": "text",
#                                 "text": otp,
#                             }
#                         ],
#                     },
#                 ],
#             },
#         }

#         headers = {
#             "Authorization": f"Bearer {settings.meta_access_token}",
#             "Content-Type": "application/json",
#         }

#         try:
#             response = httpx.post(
#                 url,
#                 json=payload,
#                 headers=headers,
#                 timeout=15,
#             )
#             response.raise_for_status()
#         except httpx.HTTPStatusError as exc:
#             # Avoid exposing provider responses or tokens to clients.
#             raise RuntimeError(
#                 f"WhatsApp API rejected the request "
#                 f"(HTTP {exc.response.status_code})"
#             ) from None
#         except httpx.RequestError:
#             raise RuntimeError(
#                 "Could not connect to WhatsApp Cloud API"
#             ) from None
