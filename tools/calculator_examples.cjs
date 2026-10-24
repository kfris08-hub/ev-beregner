const fs=require('node:fs'),path=require('node:path');
const root=path.join(__dirname,'..'),engine=require(path.join(root,'assets/calculators.js'));
const pages=JSON.parse(fs.readFileSync(path.join(root,'data/calculator-pages.json'),'utf8'));
const examples={};
for(const page of pages){const result=engine.compute(page.calculator,page.defaults);examples[page.slug]={fields:engine.definitions[page.calculator].fields,values:page.defaults,result,html:engine.render(page.calculator,result)};}
process.stdout.write(JSON.stringify(examples));
