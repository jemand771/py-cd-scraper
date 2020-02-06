def app

pipeline {
    agent any

    options {
        // i want the checkout stage to have a different name, so bye
        skipDefaultCheckout(true)
    }

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
                script {
                    app = docker.build("jemand771/cd-scraper")
                }
            }
        }

        stage('push image') {
            
            // push image only if corresponding build flag was set
            when {
                expression { return env.PUSH_TO_DOCKER_HUB }
            }
            steps {
                script {
                    docker.withRegistry('https://registry.hub.docker.com', 'docker-hub-credentials') {
                        app.push("${env.BUILD_NUMBER}")
                        app.push("${env.BRANCH}")
                    }
                }
            }
        }
    }
}