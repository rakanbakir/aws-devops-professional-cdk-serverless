from aws_cdk import(
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_kms as kms,
    aws_ssm as ssm,
    aws_secretsmanager as sm,
    core
)
import json

class RDSStack(core.Stack):
    
    def __init__(self, scope: core.Construct,id: str, vpc:ec2.Vpc, lambdasg: ec2.SecurityGroup, bastionsg: ec2.SecurityGroup, kmskey, **kwargs) -> None:
        super().__init__(scope,id,**kwargs)
        
        prj_name = self.node.try_get_context("project_name")
        env_name = self.node.try_get_context("env")
        
        db_mysql=rds.DatabaseCluster(self,'mysql',
            default_database_name=prj_name+env_name,
            engine = rds.DatabaseClusterEngine.aurora_mysql(
                version=rds.AuroraMysqlEngineVersion.VER_5_7_12
            ),
            storage_encrypted=True,
            storage_encryption_key=kmskey,
            credentials=rds.Credentials.from_generated_secret("admin",secret_name=env_name+'/db-creds'),
            instance_props=rds.InstanceProps(
                vpc=vpc,
                vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.ISOLATED),
                instance_type=ec2.InstanceType(instance_type_identifier='t3.small'),
            ),
            instances=1,
            parameter_group=rds.ParameterGroup.from_parameter_group_name(
                self,'pg-dev',
                parameter_group_name='default.aurora-mysql5.7'
            ),
            removal_policy=core.RemovalPolicy.DESTROY
        )
        
        db_mysql.connections.allow_default_port_from(lambdasg, "Access from Lambda Functions")
        db_mysql.connections.allow_default_port_from(bastionsg, "Allow from bastion host")
        
        # SSM Parameters
        ssm.StringParameter(self, 'db-host',
            parameter_name='/'+env_name+'/db-host',   
            string_value=db_mysql.cluster_endpoint.hostname                     
        )
        
        ssm.StringParameter(self,'db-name',
            parameter_name='/'+env_name+'/db-name',
            string_value=prj_name+env_name
        )