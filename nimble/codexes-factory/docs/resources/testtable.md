version_line = subprocess.check_output(["git", "describe", "--long"]).decode("utf-8").strip(

update_line = `last_modified_date.strftime("%Y-%m-%d %H:%M:%S")`

data = {"version": version_line, "last updated": update_line)

df = pd.from_dict(data)

st.table(df)
