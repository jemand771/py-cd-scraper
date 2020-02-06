pipeline {
    agent any

    stages {

        stage('checkout') {
            

            steps {
                checkout scm
            }
        }

        stage('build image') {
            
            // locally build docker image
            steps {
                echo "building image for build ${env.BUILD_NUMBER}"
                app = docker.build("jemand771/cd-scraper")
            }
        }

        stage('push image') {
            
            // push image only if corresponding build flag was set
            when {
                expression { return env.PUSH_TO_DOCKER_HUB == "True"}
            }
            steps {
                docker.withRegistry('https://registry.hub.docker.com', 'docker-hub-credentials') {
                    app.push("${env.BUILD_NUMBER}")
                    app.push("latest")
                }
            }
        }
    }
}