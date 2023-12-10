import csv


def get_moon_in_signs_interpretations(
        file_path: str = './moon_in_sign.csv'
    ):

    moon_in_signs_interpretations = {}

    with open(
        file_path, 
        mode='r', 
        encoding='utf-8'
    ) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            sign = row['sign']
            moon_in_signs_interpretations[sign] = {
                'general': row['general'],
                'favorable': row['favorable'],
                'unfavorable': row['unfavorable']
            }

    return moon_in_signs_interpretations

