import pandas as pd
from pandas import DataFrame


csv_file_before = pd.read_csv("K:\\").fillna(1)
csv_file_after = pd.read_csv("K:\\").fillna(1)

single_process_before = pd.read_csv("K:\\").fillna(1)
single_process_after = pd.read_csv("K:\\").fillna(1)

def test_step_size_change(before: DataFrame, after: DataFrame) -> bool:
    """ Check whether the test step changed """
    if after["ARIS id"].max() == before["ARIS id"].max():
        return False # --> did any fields in the test step or any other data change?
    return True

def retrieve_added_or_removed_test_steps(changed_items, before, after):
    after_size = after["ARIS id"].max()
    before_size = before["ARIS id"].max()
    diff = after_size - before_size
    if after_size > before_size:
        added = after.iloc[before_size - 1: after_size - 1]
        print(f'{diff} new test step(s) created aris_id {added["ARIS id"].values.tolist()}')
    if after_size < before_size:
        removed = before.iloc[after_size:]
        print(f'{diff} test step(s) were deleted aris_id {removed["ARIS id"].values.tolist()}')

def retrieve_modified_test_steps(changed_items, before, after):
    changes = before.eq(after)
    for col in ["Test Step", "Expected result", "Test Data"]:
        difference = changes[changes[col] == False][col]
        if difference.empty is False:
            val = difference.index.to_series()
            if val.size != 1:
                raise ValueError("Issue detected")
            changed_items.append((val.item(), col))
    return changed_items
    
def re_order(df, col):
    df['Trigger order'] = df['Trigger order'].astype('int32')
    df['Parent'] = df['Parent'].astype('int32')
    df.sort_values(by=[col], inplace=True)
    return df
    
def field_changed(changed_items: list, before: DataFrame, after: DataFrame) -> list:
    
    if test_step_size_change(before, after) is True:
        retrieve_added_or_removed_test_steps(changed_items, before, after)
    else:
        retrieve_modified_test_steps(changed_items, before, after)
    return changed_items
    

def check_test_step_single_process_change(changed_items, f1, f2):
    changed_items = field_changed(changed_items, f1, f2)
    for element in changed_items:
        index, col = element
        new_value = f2.loc[index, col]
        aris_id = f2.loc[index, "ARIS id"]
        print(f"new value '{new_value}' was found on index '{index}', column '{col}' and aris_id {aris_id}")

#check_multiple_process_change()
#csv_file['Trigger order'] = csv_file['Trigger order'].astype('int32')
#csv_file['Parent'] = csv_file['Parent'].astype('int32')
#print(csv_file.sort_values(by=['Trigger order']))
#print(csv_file.sort_values(by=['Parent']))

def main():
    changed_items = list()
    check_test_step_single_process_change(changed_items, csv_file_before, csv_file_after)
    check_test_step_single_process_change(changed_items, single_process_before, single_process_after)

if __name__ == "__main__":
    main()
