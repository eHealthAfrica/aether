check_openssl () {
    which openssl > /dev/null
}

gen_random_string () {
    openssl rand -hex 16 | tr -d "\n"
}
