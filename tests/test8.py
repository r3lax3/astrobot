import json
import hmac

data = {
    'do': 'link',
    'products': [
        {
            'name': 'Подписка на астропульс, 6 месяцев',
            'price': 5400,
            'quantity': 1,
            'paymentMethod': 4,
            'paymentObject': 4
        }
    ],
    'link_expired': '2024-02-15 23:39',
    'order_id': 'subscr:6:1060062986',
    'sys': ''
}
key = '63b90283bb6b538c4ae6ef17cbd158a8eb3c55f62d9f1c57d0a1b3b4c13c2a87'

hmac_result = Hmac.create(data, key, 'sha256')
print("HMAC result:", hmac_result)

# sign = '3aa9227aededc3d0a90915a46008ca7fe2bf1c77232a33303426eec0080f0a2a'
# print("Verify:", HmacPython.verify(data, secret_key, sign))


# class HmacPython:
#     @staticmethod
#     def create(data, key, algo="sha256"):
#         if algo not in hashlib.algorithms_available:
#             return False
#
#         def _sort(obj):
#             if isinstance(obj, dict):
#                 return sorted((k, _sort(v)) for k, v in obj.items())
#             if isinstance(obj, list):
#                 return sorted(_sort(x) for x in obj)
#             return str(obj)  # Конвертируем все значения в строки
#
#         sorted_data = _sort(data)
#         data_str = json.dumps(sorted_data, ensure_ascii=False, separators=(',', ':'))
#
#         print(data_str)  # Для сравнения с выводом PHP-версии
#
#         return hmac.new(key.encode(), data_str.encode(), algo).hexdigest()
#
#     @staticmethod
#     def verify(data, key, sign, algo="sha256"):
#         _sign = HmacPython.create(data, key, algo)
#         return _sign and (_sign.lower() == sign.lower())
#
#
# data = {
#     'do': 'link',
#     'products': [
#         {
#             'name': 'title',
#             'price': 5400,
#             'quantity': 1,
#             'paymentMethod': 4,
#             'paymentObject': 4
#         }
#     ],
#     'link_expired': '2024-02-14 04:55',
#     'order_id': 'SUBSCRIPTION_USER1060062986_12MONTH',
#     'sys': '',
#     'urlSuccess': 'https://google.com/'
# }
# # Secret key from the payment form's settings page
# secret_key = '63b90283bb6b538c4ae6ef17cbd158a8eb3c55f62d9f1c57d0a1b3b4c13c2a87'
#
#
# hashed = HmacPython.create(data, secret_key)
# print("Hash:", hashed)
#
# sign = '3aa9227aededc3d0a90915a46008ca7fe2bf1c77232a33303426eec0080f0a2a'
# print("Verify:", HmacPython.verify(data, secret_key, sign))
