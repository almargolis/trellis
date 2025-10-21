---
created_date: '2025-10-10'
published_date: '2025-10-10'
title: ai_docker_setup
updated_date: '2025-10-10'
---

+++
date = '2025-10-09T08:43:22-07:00'
draft = false
title = 'Ai_docker_setup'
summary = "Configure a fresh linux server for RAG application"
+++
## Update system

This is based on Digital Ocean typical setup when root ssh keys
have been installed.

sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    uidmap \
    dbus-user-session \
    fuse-overlayfs \
    slirp4netns \
    iptables

sudo modprobe nf_tables
sudo modprobe ip_tables
sudo modprobe xt_nat

# 3. Make them persistent
cat << EOF | sudo tee /etc/modules-load.d/docker-rootless.conf
nf_tables
ip_tables
xt_nat
EOF

adduser --gecos "AI User" aiuser
usermod -aG sudo aiuser
cp -r /root/.ssh /home/aiuser/
chown -R sysadmin:sysadmin /home/aiuser/.ssh

# edit /etc/ssh/sshd_config
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
ChallengeResponseAuthentication no
PermitEmptyPasswords no
UsePAM no

# Install Docker
vi /etc/apparmor.d/home.aiuser.bin.rootlesskit
==========
# ref: https://ubuntu.com/blog/ubuntu-23-10-restricted-unprivileged-user-namespaces
abi <abi/4.0>,
include <tunables/global>

/home/aiuser/bin/rootlesskit flags=(unconfined) {
  userns,

  # Site-specific additions and overrides. See local/README for details.
  include if exists <local/home.aiuser.bin.rootlesskit>
}
==========
sudo systemctl restart apparmor.service
apt install -y dbus-user-session
loginctl enable-linger aiuser
systemd-run --uid=$(id -u aiuser) --gid=$(id -g aiuser) --unit=user@$(id -u aiuser).service /bin/true

Logout of server and log back in as aiuser

echo $XDG_RUNTIME_DIR
should display "/run/user/1000" or other number if aiuser was not first user


curl -fsSL https://get.docker.com/rootless -o get-docker.sh
sudo sh get-docker.sh
~/bin/dockerd-rootless-setuptool.sh install
cat >> ~/.bashrc << 'EOF'
export PATH=/home/aiuser/bin:$PATH
export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock
export XDG_RUNTIME_DIR=/run/user/$(id -u)
EOF

source ~/.bashrc

systemctl --user enable docker
systemctl --user start docker

# Verify
docker --version
docker ps

## Pull and run Chroma server
docker run -d \
  --name chromadb \
  --restart unless-stopped \
  -p 127.0.0.1:8000:8000 \
  -v ~/chroma-data:/chroma/chroma \
  chromadb/chroma:latest


# Check it's running
docker ps

# View logs
docker logs chromadb