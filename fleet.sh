#!/bin/bash
INSTANCE_NAME=$1
COMMAND=$2
ORIGINFILEPATH=$3
DESTFILEPATH=$4
USER="ubuntu"

if [ "$INSTANCE_NAME" = "worker" ]; then
	INSTANCE_ID="i-0bf08f372af0a3e98"
fi

if [ "$INSTANCE_NAME" = "geocoder" ]; then
	INSTANCE_ID="i-06e043bb1530fd832"
	USER="ec2-user"
fi

if [ "$INSTANCE_NAME" = "webserver" ]; then
	INSTANCE_ID="i-041a11bd08503d040"
fi

if [ "$COMMAND" = "start" ]; then
	aws ec2 start-instances --region=us-west-2 --instance-ids=$INSTANCE_ID
	echo "waiting 25 seconds for it to start..."
	sleep 28
	echo "grabbing ip address..."
	ip=$(aws ec2 describe-instances --instance-ids=$INSTANCE_ID --region=us-west-2 | grep --max-count=1 -P --only-matching "ec2[\-\d]+\.us-west-2\.compute\.amazonaws\.com")
	echo "connecting..."
	echo "ssh -D 5000 -i ~/kuow_keys.pem ubuntu@${ip}"
	ssh -D 5000 -oStrictHostKeyChecking=no -i ~/kuow_keys.pem ${USER}@${ip}
fi

if [ "$COMMAND" = "connect" ]; then
	echo "grabbing ip address..."
	ip=$(aws ec2 describe-instances --instance-ids=$INSTANCE_ID --region=us-west-2 | grep --max-count=1 -P --only-matching "ec2[\-\d]+\.us-west-2\.compute\.amazonaws\.com")
	echo "connecting..."
	echo "ssh -D 5000 -i ~/kuow_keys.pem ubuntu@${ip}"
	ssh -D 5000 -oStrictHostKeyChecking=no -i ~/kuow_keys.pem ${USER}@${ip}
fi

if [ "$COMMAND" = "stop" ]; then
	aws ec2 stop-instances --region=us-west-2 --instance-ids=$INSTANCE_ID
fi

if [ "$COMMAND" = "scpsend" ]; then
	ip=$(aws ec2 describe-instances --instance-ids=$INSTANCE_ID --region=us-west-2 | grep --max-count=1 -P --only-matching "ec2[\-\d]+\.us-west-2\.compute\.amazonaws\.com")
        scp -i ~/kuow_keys.pem ${ORIGINFILEPATH} ${USER}@${ip}:${DESTFILEPATH}
fi

if [ "$COMMAND" = "scpfetch" ]; then
	ip=$(aws ec2 describe-instances --instance-ids=$INSTANCE_ID --region=us-west-2 | grep --max-count=1 -P --only-matching "ec2[\-\d]+\.us-west-2\.compute\.amazonaws\.com")
        scp -i ~/kuow_keys.pem ${USER}@${ip}:${ORIGINFILEPATH} ${DESTFILEPATH}
fi
