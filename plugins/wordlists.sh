#!/usr/bin/env bash
install_wordlists() {
  download_once https://wordlists-cdn.assetnote.io/data/manual/best-dns-wordlist.txt "$BB_WORDLISTS/dns/best-dns-wordlist.txt"
  download_once https://raw.githubusercontent.com/trickest/resolvers/main/resolvers.txt "$BB_WORDLISTS/resolvers/resolvers.txt"
  download_once https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/DNS/bitquark-subdomains-top100000.txt "$BB_WORDLISTS/dns/bitquark-subdomains-top100000.txt"
  download_once https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/DNS/dns-Jhaddix.txt "$BB_WORDLISTS/dns/dns-Jhaddix.txt"
  download_once https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/DNS/subdomains-top1million-110000.txt "$BB_WORDLISTS/dns/subdomains-top1million-110000.txt"

  download_once https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt "$BB_WORDLISTS/content/common.txt"
  download_once https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/directory-list-2.3-medium.txt "$BB_WORDLISTS/content/directory-list-2.3-medium.txt"
  download_once https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/raft-medium-directories.txt "$BB_WORDLISTS/content/raft-medium-directories.txt"
  download_once https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/raft-medium-files.txt "$BB_WORDLISTS/content/raft-medium-files.txt"
  download_once https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/raft-large-directories.txt "$BB_WORDLISTS/content/raft-large-directories.txt"
  download_once https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/raft-large-files.txt "$BB_WORDLISTS/content/raft-large-files.txt"
  download_once https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/burp-parameter-names.txt "$BB_WORDLISTS/params/burp-parameter-names.txt"
}
update_wordlists() {
  install_wordlists
}
doctor_wordlists() {
  [[ -f "$BB_WORDLISTS/dns/best-dns-wordlist.txt" ]] && echo "✓ assetnote dns" || echo "✗ assetnote dns"
  [[ -f "$BB_WORDLISTS/resolvers/resolvers.txt" ]] && echo "✓ resolvers" || echo "✗ resolvers"
}
