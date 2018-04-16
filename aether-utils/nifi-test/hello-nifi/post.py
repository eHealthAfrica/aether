import requests

# "password": "b05bfe75f70082e38d3e8823dc2074f7",
data = {
    "username": "admin",
    "password": "b05bfe75f70082e38d3e8823dc2074f7",
    "auth_url" : "https://hfr-sl-api-dev.ehealthafrica.org/api-auth/v1/login/",
    "poll_url": "https://hfr-sl-api-dev.ehealthafrica.org/api/v1/facilities/SLE?include=geometry%2Clocation%2Cfacility_type"
}
port = 5447
url = "http://nifi:%s/poll-api" % port
send_num = 1

def send(url, data):
    r = requests.post(url, json=data)
    print(r)
    print(r.json())


def main():
    for x in range(send_num):
        send()

if __name__ == "__main__":
    main()
