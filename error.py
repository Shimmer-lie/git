try:
    user_weight = float(input("请输入您的体重："))
    user_height = float(input("请输入您的身高："))
    user_BMI = user_weight / user_height ** 2
except ValueError:
    print("输入不为合理数字")
except ZeroDivisionError:
    print("分母不能为零")
except:
    print("发生未知错误")
else:
    print("您的BMi为：" + str(user_BMI))
finally:
    print("程序运行结束。")
