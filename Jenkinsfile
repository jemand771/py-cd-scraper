def app

pipeline {
    agent any

    parameters {
        string(name: 'branch', defaultValue: 'master', description: 'Which branch to build')
        booleanParam(name: 'push_docker', defaultValue: true, description: 'Disable to only build+test the image')
        booleanParam(name: 'push_docker_buildnum', defaultValue: true, description: 'Enable to store this build on the docker hub')
    }

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
                    if (env.BRANCH == 'master') {
                        docker.withRegistry('https://registry.hub.docker.com', 'docker-hub-credentials') {
                            app.push("${env.BRANCH}")
                        }
                    } else{
                        docker.withRegistry('https://registry.hub.docker.com', 'docker-hub-credentials') {
                            app.push("latest")
                        }
                    }
                    if(env.PUSH_BUILD){
                        docker.withRegistry('https://registry.hub.docker.com', 'docker-hub-credentials') {
                            app.push("build-${env.BUILD_NUMBER}")
                        }
                    }
                }
            }
        }
    }
}