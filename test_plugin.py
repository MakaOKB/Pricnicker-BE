import asyncio
from app.plugins.loader import PluginLoader

async def test_plugin():
    loader = PluginLoader()
    
    # 测试插件加载
    result = await loader.load_plugin('zenmux')
    print(f'ZenMux插件加载结果: {result}')
    
    if result:
        plugin = loader.loaded_plugins.get('zenmux')
        if plugin:
            print(f'插件实例: {plugin}')
            print(f'插件启用状态: {plugin.enabled}')
            
            # 测试获取模型
            try:
                models = await plugin.get_models()
                print(f'获取到 {len(models)} 个模型')
                if models:
                    print(f'前3个模型: {[m.name for m in models[:3]]}')
            except Exception as e:
                print(f'获取模型时出错: {e}')
    else:
        print('插件加载失败')

if __name__ == '__main__':
    asyncio.run(test_plugin())