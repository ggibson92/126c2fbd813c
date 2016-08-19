Personal Goal:
 - play with some new technologies to get a basic understanding of their operations

Requirements for Project:
 - build the the following requirements in the DC/OS and Mesos environment
 - build simple Python rest app with crud operations and package as a docker container and get it running.  Show the use of: flask, logging, classes, methods, etc
 - get running at a scale of 2 or 3
 - backend is not required
 - store code in github or other public git repo so the team can review it

Notes:
 - typically I would track a project like this with status, etc on Wiki.  Due to the nature of this project, this was not done
 - as the goal was a simple application the following applies:
    - full automated testing wasn't done, just enough to provide an examples
    - code to prevent CQL injection attacks wasn't created as this is a simple app, but that would need to be done to productionize this application
    - Cassandra security and hardening need to be applied
 - persistence choice: I evaluated several options for the persistence:
    - json file: this would work with setting up a volume, but this didn't provide a simple solution for fault tolerance as the code would have to handle file replication
    - mysql db: this is a popular db type, I created prototype code to play with it, but again the replication wasn't automatic and would be complicated
    - cassandra: I looked at creating a Mesos app for this as well as the DC/OS service.  I decided to use the service as it had most of what I needed pre-build it and worked well.  With Cassandra one can easily set replication per keyspace to meet the needs.   The one major draw back is that Cassandra requires more resources then other systems, but for this project, that wasn't a major concern.

Test Calls for the CRUD Operations:

- select all users (to get a starting reference): curl http://10.158.15.138:5005/users
- add a user: curl -X POST http://10.158.15.138:5005/user -d '{"name": "smithers16", "owner": "bob hope", "owner_email": "bob.hope@funny.man"}' -H "Content-Type: application/json"
- get the details for user: curl http://10.158.15.138:5005/user/smithers16
- update the user: curl -X PUT http://10.158.15.138:5005/user/smithers16 -d '{"description": "new description", "domain": "old.funny.man"}' -H "Content-Type: application/json"
- delete the user: curl -X DELETE http://10.158.15.138:5005/user/smithers16
- select all users: curl http://10.158.15.138:5005/users

Source Code Files Of Interest:
note: only calling out significant or special files:
 - ./app/gpg_user.py - This was part of my original app when I didn't have a fault tolerant persistent backend.  This stored the data in Json using a file.  I wanted to show this code off as it is loading json to classes (serializing and deserializing), it shows class inheritance, etc.
 - ./app/gpg_cassandra_utility.py - This opens the Cassandra connection with a context manager so that even if an unhandled exception occurs it will try to close the connection properly
 - ./app/gpg_cassandra.py - code for the Cassandra calls and support code
 - ./app/gpg_views.py - the Flask entry point
 - ./app/gpg_setup_keyspace.py - the code to setup the Cassandra keyspace
 - ./app/test_gpg_cassandra.py - some tests (functional tests) to provide the cassandra connections work.  This was not intended to test everything as more testing is needed (unit tests as well as more negative tests, etc).  The goal of this was just to provide an idea of how the testing works.

Build and Deployment Steps:

- Deploy the Cassandra cluster: use the DC/OS Cassandra service to set this up.
    - Note: 3 slave nodes are required even if you are only deploying 2 Cassandra nodes
    - This service handles volumes, persistence, etc
    - There is a bug with the version of DC/OS (1.7) and Mesos that I'm running with where the Cassandra instance always shows deploying and only shows a single node, but this can be ignored.
    - The keyspace will be setup below to have a replication factor of 2, so all data will be on 2 seed nodes
    - Use the DC/OS API to list the Cassandra seeds to connect to
    - After the Cassandra cluster is up and running setup the keyspace
- build the flask container:
    - download the source
    - build the docker flask image: docker build -t ggibson-flask:latest .
    - note: the image can be run for testing: docker run -d -p 5000:5000 -e contact_points='IPsOrFQDN' ggibson-flask
- upload docker image to docker hub
    - tag the docker image: docker tag <CONTAINER_ID> <repo>
    - login to docker hub: docker login
    - upload the image: docker push <repo>
- run the docker image so we can deploy the database: docker run -d -p 5000:5000 -e contact_points='IPsOrFQDN' ggibson-flask
    - note: this only needs to happen once
    - now connect into it: sudo docker exec -i -t <CONTAINER_ID> /bin/bash
    - run the Cassandra setup script: python /app/app/gpg_setup_keyspace.py
- deploy a Mesos app to run the flask application using the Json below:

{
  "id": "/flask",
  "cmd": null,
  "cpus": 1,
  "mem": 128,
  "disk": 0,
  "instances": 3,
  "constraints": [
    [
      "hostname",
      "UNIQUE"
    ]
  ],
  "container": {
    "type": "DOCKER",
    "volumes": [],
    "docker": {
      "image": "ggibson/93493b1fd5ca",
      "network": "BRIDGE",
      "portMappings": [
        {
          "containerPort": 5000,
          "hostPort": 0,
          "servicePort": 10000,
          "protocol": "tcp",
          "labels": {
            "VIP_0": "10.158.15.138:5005"
          }
        }
      ],
      "privileged": false,
      "parameters": [],
      "forcePullImage": true
    }
  },
  "healthChecks": [
    {
      "path": "/",
      "protocol": "HTTP",
      "portIndex": 0,
      "gracePeriodSeconds": 300,
      "intervalSeconds": 60,
      "timeoutSeconds": 20,
      "maxConsecutiveFailures": 3,
      "ignoreHttp1xx": false
    }
  ],
  "env": {
    "contact_points": "10.158.15.83,10.158.15.138"
  }
}
