# BBKit recon workstation image (Ubuntu + Go tools subset).
# For VPS / CI. Not a full AI agent image — bind-mount BB_ROOT for data.

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    BB_ROOT=/data/BugBounty \
    GOPATH=/opt/go \
    PATH=/usr/local/go/bin:/opt/go/bin:/opt/bbkit/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl wget git jq python3 python3-pip \
      build-essential libpcap-dev nmap unzip \
    && rm -rf /var/lib/apt/lists/*

# Go
ARG GO_VERSION=1.24.4
RUN ARCH=$(dpkg --print-architecture) \
    && case "$ARCH" in amd64) GA=amd64;; arm64) GA=arm64;; *) GA=amd64;; esac \
    && curl -fsSL "https://go.dev/dl/go${GO_VERSION}.linux-${GA}.tar.gz" -o /tmp/go.tgz \
    && tar -C /usr/local -xzf /tmp/go.tgz \
    && rm /tmp/go.tgz

# Core ProjectDiscovery tools
RUN go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest \
 && go install github.com/projectdiscovery/httpx/cmd/httpx@latest \
 && go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest \
 && go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest \
 && go install github.com/projectdiscovery/katana/cmd/katana@latest \
 && go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest \
 && go install github.com/lc/gau/v2/cmd/gau@latest \
 && go install github.com/tomnomnom/waybackurls@latest \
 && go install github.com/tomnomnom/anew@latest \
 && go install github.com/ffuf/ffuf/v2@latest

WORKDIR /opt/bbkit
COPY . /opt/bbkit/

RUN mkdir -p /data/BugBounty/bin /data/BugBounty/output /data/BugBounty/engagements \
      /data/BugBounty/config /data/BugBounty/lib /data/BugBounty/recon /data/BugBounty/plugins \
      /data/BugBounty/skills /data/BugBounty/templates /data/BugBounty/logs \
 && cp -R /opt/bbkit/lib /opt/bbkit/recon /opt/bbkit/plugins /opt/bbkit/config \
         /opt/bbkit/skills /opt/bbkit/templates /data/BugBounty/ \
 && cp /opt/bbkit/bin/bb /data/BugBounty/bin/bb \
 && chmod +x /data/BugBounty/bin/bb /data/BugBounty/recon/* \
 && ln -sf /data/BugBounty/bin/bb /usr/local/bin/bb

WORKDIR /data/BugBounty
VOLUME ["/data/BugBounty/output", "/data/BugBounty/engagements"]

EXPOSE 8787

# Default: show help. Override: bb full … or bb dashboard --host 0.0.0.0
ENTRYPOINT ["bb"]
CMD ["help"]
