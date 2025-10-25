from code import calculate_requirements

def test_redstone_torch():
    recipes = {'redstone_torch': {'stick': 1, 'redstone': 1}}
    result = calculate_requirements(recipes, 'redstone_torch', 10)
    assert result == {'stick': 10, 'redstone': 10}
    print('test_redstone_torch passed:', result)
if __name__ == '__main__':
    test_redstone_torch()
