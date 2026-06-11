请制定一个详细的计划，输出到 [todo](docs/todo) ，我需要你完成以下几个任务：
1. [dynamic-tennis](dynamic-tennis) 是我开发的网球机器人项目，通过mujoco的仿真环境来训练控制策略，既可以通过仿真环境里的球速、机器人速度的真值来训练，也有通过仿真环境拍的照片来模拟真实环境通过图形处理给机器人提供感知的输入来模拟真实场景的感知控制。请将 [dynamic-tennis](dynamic-tennis) 这个项目的技术栈全部写成标准的skills
2. 我需要你通过sports-robot这个项目的plugins及skills自己搭建一个新的项目放到新的文件夹 tennis-robot，这个项目的搭建只可以通过sports-robot的plugins或skills不可以直接参考 [dynamic-tennis](dynamic-tennis) ，因为我们考察的是sports-robot这个项目自己搭建球类机器人项目的能力。你可以设计一个循环，让sports-robot自己搭建项目，遇到问题搭建不下去时，将 [dynamic-tennis](dynamic-tennis) 这个项目的技术栈继续沉淀为skills；直到能通过sports-robot本身就能搭建出类似 [dynamic-tennis](dynamic-tennis) 功能的项目，并且性能不能比原先差
3. 将上面1和2步骤的这种功能写成plugin或者skills，这个plugin可以将其他的球类机器人项目沉淀、借鉴、融合、补充成sports-robot的skills，使得类似球类机器人的项目可以直接通过sports-robot的skills或plugin来搭建，逐渐增强它的功能

 


 
我让大模型执行了两个任务，一个是 [tennis-robot能力沉淀与自举计划.md](sports-robot/docs/todo/tennis-robot能力沉淀与自举计划.md) 大模型生成了项目 [tennis-robot](sports-robot/tennis-robot/)  里面有开发日志文档；另一个任务是 [开源球类机器人项目吸收与超越计划.md](sports-robot/docs/todo/开源球类机器人项目吸收与超越计划.md) 并让大模型吸收和超越  [dynamic-tennis](sports-robot/dynamic-tennis/) 后来又中途发现了 [dynamic-tennis-v2](sports-robot/dynamic-tennis-v2/) 吸收和超越。聊天记录为 [完成网球机器人计划任务.md](sports-robot/docs/todo/完成网球机器人计划任务.md) 

请检查分析验证，这两个任务是否正确完成？新生成的项目是否是通过sports-robot的skills和plugins来完成的？
这两个任务形成的skills和plugins是否有冲突，是否需要优化？
在吸收开源项目时，需要考虑这些步骤（项目分析->流程拆解->技能及插件的提取->技能及插件的合并或新建->技能及插件的测试）
在复现和超越开源项目时，可以参考这些步骤（环境配置->基于sports-robot的技能及插件的项目设计->项目实现->功能测试->性能评估->性能优化->文档生成与更新），其中性能优化主要针对超越开源项目的目的，性能优化与性能评估可以设计一个迭代循环，指导超越开源项目达到指定的目标（如达到1.3x开源项目原有性能）。
最后根据新实现的功能更新readme


      2    "env": {
      3 -    "ANTHROPIC_AUTH_TOKEN": "sk-IX3qC7nIDRHmWhRBj1sPmzb9Yuh4M0ebDQsdrScHHbEbRfyE",                                                                                                   
      4 -    "ANTHROPIC_BASE_URL": "https://rsxermu666.cn",                                                                                                                                   
      5 -    "ANTHROPIC_MODEL": "claude-fable-5",                                                                                                                                             
      6 -    "ANTHROPIC_SMALL_FAST_MODEL": "claude-fable-5"                                                                                                                                   
      3 +    "ANTHROPIC_AUTH_TOKEN": "sk-e6983a31d5c64ddebdac10fdf514e162",                                                                                                                   
      4 +    "ANTHROPIC_BASE_URL": "https://opencode.cn/v1",                                                                                                                                  
      5 +    "ANTHROPIC_MODEL": "glm-5",                                                                                                                                                      
      6 +    "ANTHROPIC_SMALL_FAST_MODEL": "glm-5"                                                                                                                                            
      7    },

{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "sk-IX3qC7nIDRHmWhRBj1sPmzb9Yuh4M0ebDQsdrScHHbEbRfyE",
    "ANTHROPIC_BASE_URL": "https://rsxermu666.cn",
    "ANTHROPIC_MODEL": "claude-fable-5",
    "ANTHROPIC_SMALL_FAST_MODEL": "claude-fable-5"
  },
  "permissions": {
    "defaultMode": "bypassPermissions"
  },
  "model": "claude-fable-5",
  "skipDangerousModePermissionPrompt": true
}

claude --session 0dc51f71-17ae-48be-ae2e-ab49ddeda40d --dangerously-skip-permissions