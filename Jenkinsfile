#!groovy

pipeline {
    environment {
        VERSION = ''
    }

    agent { label 'master' }

    stages {
        stage('Build Docker images') {
            steps {
                dir('django'){
                    script {
                        docker.withRegistry("https://docker.crosslang.com", "docker-crosslang-com") {

                            def customImage = docker.build("ctlg-manager/django:${env.BUILD_ID}", "-f Dockerfile.prod .")
                            customImage.push()
                        }
                    }
                }
            }
        }
    }

    post {
        success {
            slackSend (color: '#36A64F', message: "SUCCESSFUL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
        }
        failure {
            slackSend (color: '#FF0000', message: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
        }
    }

}

