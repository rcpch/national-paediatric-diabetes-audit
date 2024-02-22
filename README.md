# National Paediatric Diabetes Audit (NPDA)

A django rest framework project containing all the measures for the NPDA

It needs some environment variables stored in ```envs/.env``` to work (see example.env)

To get running it is all dockerised:

```command
chmod +x s/*.*
s/docker-up
```

Either navigate to the platform:
`https://npda.localhost/home#`

or to the Swagger browsable API:
`https://npda.localhost/swagger-ui/`

or to the docs:
`http://0.0.0.0:8007/`