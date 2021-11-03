import os

from utils import save_to_numpy_array, create_csv_reader, default_arg_parser, split_by_label

column_names = [
    'S1',
    'C1',
    'S2',
    'C2',
    'S3',
    'C3',
    'S4',
    'C4',
    'S5',
    'C5',
    'label',
]


def convert_format(config):
    read_csv = create_csv_reader(
            config.source,
            header=None,
            index_col=None,
            names=column_names)

    train_df = read_csv('poker-hand-training-true.data')
    test_df = read_csv('poker-hand-testing.data')
    
    train_data_df, train_labels_df = split_by_label(train_df)
    test_data_df, test_labels_df = split_by_label(test_df)

    save_to_numpy_array(os.path.join(config.outputdirectory, 'poker'), {
        'train-data': train_data_df,
        'train-labels': train_labels_df,
        'test-data': test_data_df,
        'test-labels': test_labels_df,
    })


if __name__ == '__main__':
    args = default_arg_parser(
            source_default='https://archive.ics.uci.edu/ml/machine-learning-databases/poker',
    ).parse_args()
    
    convert_format(args)
