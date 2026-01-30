import os
import subprocess
import shutil
from flask import Blueprint, render_template, request, jsonify
from CTFd.utils.decorators import admins_only
from CTFd.utils import get_config
from pathlib import Path

admin_bp = Blueprint(
    'challenge_deployer_admin',
    __name__,
    template_folder='templates',
    static_folder='assets',
    url_prefix='/admin/challenge-deployer'
)

CHALL_MANAGER_BASE = "/opt/ctfd-chall-manager/hack/desafios"
EXAMPLE_DIR = os.path.join(CHALL_MANAGER_BASE, "example")


@admin_bp.route('/')
@admins_only
def admin_view():
    """Admin page to manage challenge deployments"""
    return render_template('challenge_deployer_admin.html')


@admin_bp.route('/api/challenges', methods=['GET'])
@admins_only
def list_challenges():
    """List all deployed challenges"""
    try:
        challenges = []
        if os.path.exists(CHALL_MANAGER_BASE):
            for item in os.listdir(CHALL_MANAGER_BASE):
                item_path = os.path.join(CHALL_MANAGER_BASE, item)
                if os.path.isdir(item_path) and item != "example":
                    challenges.append({
                        'name': item,
                        'path': item_path
                    })
        return jsonify({'success': True, 'challenges': challenges})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/deploy', methods=['POST'])
@admins_only
def deploy_challenge():
    """
    Deploy a new challenge to the registry
    Expected JSON:
    {
        "challenge_name": "web01",
        "docker_image": "lukerking/sqli:latest",
        "internal_port": "80",
        "hostname": "desafios.ctfgthc.com.br",
        "protocol": "tcp",
        "registry": "localhost:5000/"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['challenge_name', 'docker_image', 'internal_port']
        for field in required:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório: {field}'
                }), 400
        
        challenge_name = data['challenge_name']
        docker_image = data['docker_image']
        internal_port = data['internal_port']
        hostname = data.get('hostname', 'desafios.ctfgthc.com.br')
        protocol = data.get('protocol', 'tcp')
        registry = data.get('registry', 'localhost:5000/')
        
        # Ensure registry ends with /
        if not registry.endswith('/'):
            registry += '/'
        
        # Create challenge directory
        challenge_dir = os.path.join(CHALL_MANAGER_BASE, challenge_name)
        
        if os.path.exists(challenge_dir):
            return jsonify({
                'success': False,
                'error': f'Desafio "{challenge_name}" já existe!'
            }), 400
        
        # Check if example directory exists
        if not os.path.exists(EXAMPLE_DIR):
            return jsonify({
                'success': False,
                'error': f'Diretório example não encontrado: {EXAMPLE_DIR}'
            }), 500
        
        # Copy example directory
        shutil.copytree(EXAMPLE_DIR, challenge_dir)
        
        # Modify Pulumi.yaml
        pulumi_yaml_path = os.path.join(challenge_dir, 'Pulumi.yaml')
        modify_pulumi_yaml(pulumi_yaml_path, challenge_name)
        
        # Modify build.sh
        build_sh_path = os.path.join(challenge_dir, 'build.sh')
        modify_build_sh(build_sh_path, challenge_name, registry)
        
        # Modify main.go
        main_go_path = os.path.join(challenge_dir, 'main.go')
        modify_main_go(
            main_go_path,
            docker_image,
            internal_port,
            hostname,
            protocol
        )
        
        # Make build.sh executable
        os.chmod(build_sh_path, 0o755)
        
        # Execute build.sh
        result = execute_build_script(challenge_dir, registry)
        
        if result['success']:
            registry_url = f"{registry}gthc/{challenge_name}:latest"
            return jsonify({
                'success': True,
                'message': 'Desafio criado e enviado para o registry com sucesso!',
                'registry_url': registry_url,
                'output': result['output']
            })
        else:
            # Cleanup on failure
            shutil.rmtree(challenge_dir, ignore_errors=True)
            return jsonify({
                'success': False,
                'error': f'Erro ao executar build.sh: {result["error"]}',
                'output': result.get('output', '')
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500


@admin_bp.route('/api/delete/<challenge_name>', methods=['DELETE'])
@admins_only
def delete_challenge(challenge_name):
    """Delete a challenge directory"""
    try:
        challenge_dir = os.path.join(CHALL_MANAGER_BASE, challenge_name)
        
        if not os.path.exists(challenge_dir):
            return jsonify({
                'success': False,
                'error': 'Desafio não encontrado'
            }), 404
        
        if challenge_name == "example":
            return jsonify({
                'success': False,
                'error': 'Não é possível deletar o diretório example'
            }), 400
        
        shutil.rmtree(challenge_dir)
        
        return jsonify({
            'success': True,
            'message': f'Desafio "{challenge_name}" deletado com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def modify_pulumi_yaml(file_path, challenge_name):
    """Modify Pulumi.yaml with the challenge name"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace name
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if line.startswith('name:'):
            new_lines.append(f'name: {challenge_name}')
        else:
            new_lines.append(line)
    
    with open(file_path, 'w') as f:
        f.write('\n'.join(new_lines))


def modify_build_sh(file_path, challenge_name, registry):
    """Modify build.sh with the challenge name and registry"""
    content = f"""#!/bin/bash

CGO_ENABLED=0 go build -o main main.go
REGISTRY=${{REGISTRY:-"{registry}"}}

cp Pulumi.yaml Pulumi.yaml.bkp
yq -iy '.runtime = {{"name": "go", "options": {{"binary": "./main"}}}}' Pulumi.yaml

oras push --insecure \\
  "${{REGISTRY}}gthc/{challenge_name}:latest" \\
  --artifact-type application/vnd.ctfer-io.scenario \\
  main:application/vnd.ctfer-io.file \\
  Pulumi.yaml:application/vnd.ctfer-io.file

rm main
mv Pulumi.yaml.bkp Pulumi.yaml
"""
    
    with open(file_path, 'w') as f:
        f.write(content)


def modify_main_go(file_path, docker_image, internal_port, hostname, protocol):
    """Modify main.go with challenge configuration"""
    content = f"""package main

import (
        "fmt"
        "strconv"

        "github.com/ctfer-io/chall-manager/sdk"
        "github.com/pulumi/pulumi-docker/sdk/v4/go/docker"
        "github.com/pulumi/pulumi/sdk/v3/go/pulumi"
)

func main() {{
        sdk.Run(func(req *sdk.Request, resp *sdk.Response, opts ...pulumi.ResourceOption) error {{

                // check defaults
                image, ok := req.Config.Additional["image"]
                if !ok {{
                        image = "{docker_image}"
                }}

                portStr, ok := req.Config.Additional["port"]
                if !ok {{
                        portStr = "{internal_port}"
                }}

                port, err := strconv.Atoi(portStr)
                if err != nil {{
                        return err
                }}

                hostname, ok := req.Config.Additional["hostname"]
                if !ok {{
                        hostname = "{hostname}"
                }}

                protocol_port, ok := req.Config.Additional["protocol_port"]
                if !ok {{
                        protocol_port = "{protocol}"
                }}

                // pull image locally
                img, err := docker.NewRemoteImage(req.Ctx, "challenge-image", &docker.RemoteImageArgs{{
                        Name:        pulumi.String(image),
                        Platform:    pulumi.String("linux/amd64"),
                        KeepLocally: pulumi.Bool(true), // do not remove image
                }})
                if err != nil {{
                        return err
                }}

                // create a container
                container, err := docker.NewContainer(req.Ctx, "challenge-container", &docker.ContainerArgs{{
                        Image: img.ImageId,
                        Name:  pulumi.Sprintf("challenge-%s", req.Config.Identity),
                        Ports: docker.ContainerPortArray{{
                                docker.ContainerPortArgs{{
                                        Protocol: pulumi.String(protocol_port),
                                        Internal: pulumi.Int(port),
                                }},
                        }},
                        Rm: pulumi.Bool(true),
                }})
                if err != nil {{
                        return err
                }}

                resp.ConnectionInfo = container.Ports.ApplyT(func(ports []docker.ContainerPort) string {{
                        port := ports[0].External
                        url := fmt.Sprintf("%s %d", hostname, *port)
                        return url
                }}).(pulumi.StringOutput)

                return nil
        }})
}}
"""
    
    with open(file_path, 'w') as f:
        f.write(content)


def execute_build_script(challenge_dir, registry):
    """Execute the build.sh script in the challenge directory"""
    try:
        env = os.environ.copy()
        env['REGISTRY'] = registry
        
        result = subprocess.run(
            ['bash', 'build.sh'],
            cwd=challenge_dir,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
            env=env
        )
        
        if result.returncode == 0:
            return {
                'success': True,
                'output': result.stdout + result.stderr
            }
        else:
            return {
                'success': False,
                'error': f'Exit code: {result.returncode}',
                'output': result.stdout + result.stderr
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Timeout: Build script demorou mais de 5 minutos'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
