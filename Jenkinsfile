pipeline {
  agent any
  stages {
    stage('Build') {
      parallel {
        stage('Build') {
          steps {
            sh 'docker-compose -f ./globalwhitelist/docker-compose.yaml up -d --build'
            sh 'docker-compose -f test.yaml up -d --build'
          }
        }

        stage('Tagging') {
          steps {
            sh 'docker tag odoo_staging_odoo gechcode/odoo_15_staging:"$BUILD_NUMBER"'
          }
        }

      }
    }

    stage('Test') {
      steps {
        echo 'Testing..'
      }
    }

    stage('Deploy') {
      steps {
        echo 'Deploying....'
      }
    }

  }
  environment {
    registry = 'gechcode/odoo_15'
    registryCredential = '7249de4f-7415-4d48-9e68-6f77218f9e51'
  }
  options {
    buildDiscarder(logRotator(numToKeepStr: '5', daysToKeepStr: '5'))
    timestamps()
  }
}