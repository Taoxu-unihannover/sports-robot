请制定一个详细的计划，输出到 [todo](docs/todo) ，我需要你完成以下几个任务：
1. [dynamic-tennis](dynamic-tennis) 是我开发的网球机器人项目，通过mujoco的仿真环境来训练控制策略，既可以通过仿真环境里的球速、机器人速度的真值来训练，也有通过仿真环境拍的照片来模拟真实环境通过图形处理给机器人提供感知的输入来模拟真实场景的感知控制。请将 [dynamic-tennis](dynamic-tennis) 这个项目的技术栈全部写成标准的skills
2. 我需要你通过sports-robot这个项目的plugins及skills自己搭建一个新的项目放到新的文件夹 tennis-robot，这个项目的搭建只可以通过sports-robot的plugins或skills不可以直接参考 [dynamic-tennis](dynamic-tennis) ，因为我们考察的是sports-robot这个项目自己搭建球类机器人项目的能力。你可以设计一个循环，让sports-robot自己搭建项目，遇到问题搭建不下去时，将 [dynamic-tennis](dynamic-tennis) 这个项目的技术栈继续沉淀为skills；直到能通过sports-robot本身就能搭建出类似 [dynamic-tennis](dynamic-tennis) 功能的项目，并且性能不能比原先差
3. 将上面1和2步骤的这种功能写成plugin或者skills，这个plugin可以将其他的球类机器人项目沉淀、借鉴、融合、补充成sports-robot的skills，使得类似球类机器人的项目可以直接通过sports-robot的skills或plugin来搭建，逐渐增强它的功能


