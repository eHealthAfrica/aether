#! /usr/bin/python

import json
from utils import (
  get_kernel_auth_header,
  kernel_data_request
)


sample = {
  "id": "a5336669-605c-4a65-ab4c-c0318e28115b",
  "facility_name": "Primary Health Care Abuja",
  "staff": {
    "doctor": 15,
    "nurse": 40
  },
  "opening_hour": "7AM working days",
  "patient": {
    "patient_id": "c55021d0-cc34-46ba-ac5b-4cd5bcbde3f9",
    "name": "Nancy William"
  }
}


try:
  resp = kernel_data_request(
      url=f'submissions/',
      method='post',
      headers=get_kernel_auth_header,
      data=json.dumps(sample),
  )
  print('RESP>>>>', resp.json())
except Exception as e:
  print('ERRROR>>>>>', str(e))
