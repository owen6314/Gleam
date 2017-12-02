def get_model_data(obj, fields):
  data = dict()
  for field in fields:
    data[field] = getattr(obj, field)
  return data

def post_model_data(obj, form, fields=None):
  # 把form里经过清洗的数据保存到obj里

  if not fields:
    fields = form.cleaned_data.keys()
  for field in fields:
    setattr(obj, field, form.cleaned_data[field])
  obj.save()
