node {
  if (env.BRANCH_NAME == "command"){
    properties([
      parameters([string(defaultValue: 'staging', description: '', name:'enviroment'),
      string(defaultValue: 'python manage.py migrate', description: '', name:'djangocommand')])
    ])
  }
  checkout scm
  withCredentials([usernamePassword(credentialsId: 'docker', passwordVariable: 'DOCKER_PASSWORD', usernameVariable: 'DOCKER_USERNAME')]) {
    sh("docker login -u ${env.DOCKER_USERNAME} -p ${env.DOCKER_PASSWORD} registry.aliyuncs.com")
  }
  sh("docker build -t ndpuzsys:latest .")
  if (env.BRANCH_NAME == 'command'){
    if (params.enviroment == 'production'){
      withCredentials([usernamePassword(credentialsId: 'redis_production', passwordVariable: 'REDIS_AUTH', usernameVariable: 'REDIS_USER'),
        usernamePassword(credentialsId: 'mysql_production', passwordVariable: 'MYSQL_AUTH', usernameVariable: 'MYSQL_USER')]) {
        sh("docker run -e TARGET=k8s-production -e MYSQL_AUTH=${env.MYSQL_AUTH} -e REDIS_AUTH=${env.REDIS_AUTH} ndpuzsys:latest ${params.djangocommand}")
      }
    } else {
      withCredentials([usernamePassword(credentialsId: 'redis', passwordVariable: 'REDIS_AUTH', usernameVariable: 'REDIS_USER'),
        usernamePassword(credentialsId: 'mysql', passwordVariable: 'MYSQL_AUTH', usernameVariable: 'MYSQL_USER')]) {
        sh("docker run -e TARGET=k8s -e MYSQL_AUTH=${env.MYSQL_AUTH} -e REDIS_AUTH=${env.REDIS_AUTH} ndpuzsys:latest ${params.djangocommand}")
      }
    }
  } else {
    //withCredentials([usernamePassword(credentialsId: 'redis', passwordVariable: 'REDIS_AUTH', usernameVariable: 'REDIS_USER'),
    //  usernamePassword(credentialsId: 'mysql', passwordVariable: 'MYSQL_AUTH', usernameVariable: 'MYSQL_USER')]) {
    //  sh("docker run -e TARGET=k8s -e MYSQL_AUTH=${env.MYSQL_AUTH} -e REDIS_AUTH=${env.REDIS_AUTH} ndpuzsys:latest python manage.py test -t . --keepdb --exclude-tag=B --exclude-tag=C")
    //}
    sh("docker tag ndpuzsys:latest registry.aliyuncs.com/ndpuz-img/ndpuzsys:`git rev-parse HEAD`")
    sh("docker push registry.aliyuncs.com/ndpuz-img/ndpuzsys:`git rev-parse HEAD`")
  }

  if (env.BRANCH_NAME == "master") {
    stage('Deploy to kubenetes:'){
      gitCommit = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
      build job: 'ndpuzsys-deployment/staging', parameters: [[$class: 'StringParameterValue', name: 'commit_id', value: gitCommit]]
    }
  }
}

