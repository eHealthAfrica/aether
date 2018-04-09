import requests



port = 5446
url = "http://nifi:%s/app/json" % port
payload = [
  {
    "person": {
      "forename": "Sejflsd Dljljkf",
      "surname": "Lfdjk",
      "age": {
        "years": "43"
      },
      "gender": "Male",
      "mothersForename": "Fokdsh",
      "location": {
        "zone": "mosango",
        "area": "muluma",
        "village": "kisala-lupa"
      },
      "birthYear": 1972
    },
    "participant": {
      "memberType": "resident",
      "screenings": {
        "maect": {
          "sessionType": "doorToDoor",
          "group": "2016-04-08T05:17:24.338Z",
          "result": "negative"
        }
      },
      "screeningLocation": {
        "zone": "mosango",
        "area": "muluma",
        "village": "kisala-lupa"
      },
      "hatId": "JHFNJDT1982M",
      "version": 3,
      "geoLocation": {
        "accuracy": 3,
        "latitude": -4.7555159,
        "longitude": 18.0578531,
        "timestamp": 1460092843080
      }
    },
    "type": "participant",
    "dateCreated": "2016-04-08T05:20:43.804Z",
    "dateModified": "2016-04-08T06:53:31.706Z",
    "_id": "participant-jhfnjdt1982m",
    "_rev": "2-2a896000d68883bb22ac3aa80dff71a6"
  },
  {
    "person": {
      "forename": "Ouhkjk",
      "surname": "Okjnnd",
      "age": {
        "years": "48"
      },
      "gender": "Female",
      "mothersForename": "Mibibi",
      "location": {
        "zone": "mosango",
        "area": "muluma",
        "village": "kisala-lupa"
      },
      "birthYear": 1968
    },
    "participant": {
      "memberType": "resident",
      "screenings": {
        "maect": {
          "sessionType": "doorToDoor",
          "group": "2016-04-08T05:17:24.338Z",
          "result": "negative"
        }
      },
      "screeningLocation": {
        "zone": "mosango",
        "area": "muluma",
        "village": "kisala-lupa"
      },
      "hatId": "HFJPWNX1968M",
      "version": 3,
      "geoLocation": {
        "accuracy": 3,
        "latitude": -4.7555187,
        "longitude": 18.0578309,
        "timestamp": 1460093149057
      }
    },
    "type": "participant",
    "dateCreated": "2016-04-08T05:25:50.049Z",
    "dateModified": "2016-04-08T06:53:44.818Z",
    "_id": "participant-hfjpwnx1968m",
    "_rev": "2-2c87605ba352bda48f2fc12a540d88a0"
  }
]

send_num = 11

def send():
    r = requests.post(url, json=payload)
    print(r)


def main():
    for x in range(send_num):
        send()

if __name__ == "__main__":
    main()
