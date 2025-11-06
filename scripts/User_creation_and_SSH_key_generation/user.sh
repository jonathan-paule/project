#!/bin/bash

# Usage: ./create_docker_user.sh <username>
USERNAME=$1

if [ -z "$USERNAME" ]; then
	  echo "Usage: $0 <username>"
	    exit 1
fi

# Check if the group exists
if ! getent group "$USERNAME" > /dev/null; then
	    echo "Group '$USERNAME' does not exist. Creating it..."
	        sudo groupadd "$USERNAME"
		    if [ $? -ne 0 ]; then
			            echo "Error: Failed to create group '$USERNAME'."
				            exit 1
					        fi
					else
						    echo "Group '$USERNAME' already exists."
fi
# Check if user exists

OUTPUT=$(eval "getent passwd $USERNAME")
if [ -z "$OUTPUT" ]; then
	    echo "Creating user $USERNAME..."
	        sudo useradd -m -s /bin/bash -g "$USERNAME" "$USERNAME"
	else
		    echo "User $USERNAME already exists."
		        exit 100
fi
# Add user to docker group if not already
if groups "$USERNAME" | grep -qw "docker"; then
	  echo "User $USERNAME is already in docker group."
  else
	    echo "Adding $USERNAME to docker group..."
	      sudo usermod -aG docker "$USERNAME"
fi

# Setup SSH directory
SSH_DIR="/home/$USERNAME/.ssh"
sudo mkdir -p "$SSH_DIR"
sudo chmod 700 "$SSH_DIR"
sudo chown "$USERNAME:$USERNAME" "$SSH_DIR"

# Generate SSH keypair
KEY_FILE="/tmp/${USERNAME}_id_rsa"
if [ -f "$KEY_FILE" ]; then
	  rm -f "$KEY_FILE"*
fi

ssh-keygen -t rsa -b 4096 -f "$KEY_FILE" -N "" >/dev/null 2>&1

# Copy public key to authorized_keys
sudo mkdir -p "$SSH_DIR"
sudo cp "${KEY_FILE}.pub" "$SSH_DIR/authorized_keys"
sudo chmod 600 "$SSH_DIR/authorized_keys"
sudo chown "$USERNAME:$USERNAME" "$SSH_DIR/authorized_keys"

# Show private key
echo "Private key for user $USERNAME:"
cat "$KEY_FILE"

# Optional: Secure cleanup
echo "Private key saved at $KEY_FILE"
echo ">>> Please copy it now and delete the file if needed! <<<"


python3 AWS_SES.py "$KEY_FILE"    # keep this AES_SES.py file saved in your local
