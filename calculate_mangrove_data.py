import ee
import streamlit as st
import geemap

geemap.ee_initialize()

@st.cache_data
def get_data(image_url):
    maxPixels = 1e10
    carbonStock_MgC_perHectare = {
        'mean': 1.087,
        'stdev': 0.584,
    }
    
    data = {}
    pred = ee.Image(image_url).select('prediction')
  
    crsTransform = pred.projection().getInfo()['transform']
  
    pixelCount = pred.reduceRegion(
        reducer = ee.Reducer.frequencyHistogram(),
        crs = pred.projection(),
        crsTransform = crsTransform,
        maxPixels = maxPixels
    )

    names_mangroves = ['Delta','Estuary','Lagoon','OpenCoast']
    names_nonmangroves = ['Water','NonMangroves','Other']
    names_classes = names_mangroves+names_nonmangroves
    data['size_mangroves'] = len(names_mangroves)
    data['names_classes'] = names_classes
  
    isMangrove = [1 for i in names_mangroves]+[0 for i in names_nonmangroves]
    data['isMangrove'] = isMangrove

    seq = range(0, len(names_classes))
  
    # Area
    def getArea(classIndex):
        pixelArea = ee.Image.pixelArea()
        class_no = pred.eq(ee.Number(classIndex).int())
        area = pixelArea.updateMask(class_no).reduceRegion(
            reducer = ee.Reducer.sum(),
            crs = pred.projection(),
            crsTransform =  crsTransform,
            maxPixels = maxPixels
        )
        return area.getNumber('area')
    areas = list(map(getArea, seq))
    data['areaSqMeter'] = areas
    
    # Carbon Stock
    def getCarbonStock(areaHectare):
        carbonStockMean = areaHectare.multiply(carbonStock_MgC_perHectare['mean'])
        carbonStockStandardDeviation = areaHectare.multiply(carbonStock_MgC_perHectare['stdev'])
        return [carbonStockMean,carbonStockStandardDeviation]
    carbonStock = list(map(
        lambda number: getCarbonStock(areas[number].divide(1e4)),
        [i for i in range(len(names_mangroves))]))
    data['carbonStock'] = carbonStock+[[0.0, 0.0] for i in names_nonmangroves]
  
    # Pixel Count
    def getPixelCount(classIndex):
        return ee.Dictionary(pixelCount.get('prediction')).get(ee.Number(classIndex).format('%.1f'),0)
    data['pixelCount'] = list(map(getPixelCount,seq))
    
    # Image Dimensions
    data['pixelDimensions'] = pred.getInfo()['bands'][0]['dimensions']
  
    return ee.Dictionary(data).getInfo()

class Mangrove_data:
    def __init__(self, image_prefix, location, model, year_list):
        #first year
        data = get_data(image_prefix+location+'_'+year_list[0]+'_'+model)
    
        pixel_dimensions = data['pixelDimensions']

        classes_list = data['names_classes']
        size_mangroves = data['size_mangroves']
        
        mean_list = [sum([data['carbonStock'][i][0] for i in range(len(classes_list))])]
        stddev_list = [sum([data['carbonStock'][i][1] for i in range(len(classes_list))])]
        
        mean_dict,stddev_dict,area_dict,pixelCount_dict = {},{},{},{}

        for i in range(len(classes_list)):
            mean_dict[classes_list[i]] = [data['carbonStock'][i][0]]
            stddev_dict[classes_list[i]] = [data['carbonStock'][i][1]]
            area_dict[classes_list[i]] = [data['areaSqMeter'][i]]
            pixelCount_dict[classes_list[i]] = [data['pixelCount'][i]]

        # subsequent years
        for year_temp in year_list[1:]:
            data = get_data(image_prefix+location+'_'+year_temp+'_'+model)
            mean_list = mean_list + [sum([data['carbonStock'][i][0] for i in range(len(classes_list))])]
            stddev_list = stddev_list + [sum([data['carbonStock'][i][1] for i in range(len(classes_list))])]
            for i in range(len(classes_list)):
                mean_dict[classes_list[i]] = mean_dict[classes_list[i]] + [data['carbonStock'][i][0]]
                stddev_dict[classes_list[i]] = stddev_dict[classes_list[i]] + [data['carbonStock'][i][1]]
                area_dict[classes_list[i]] = area_dict[classes_list[i]] + [data['areaSqMeter'][i]]
                pixelCount_dict[classes_list[i]] = pixelCount_dict[classes_list[i]] + [data['pixelCount'][i]]
        
        self.pixel_dimensions = pixel_dimensions
        self.legend_dict = {
            'Delta': '80D604',
            'Estuary': '01BD7C',
            'Lagoon': '36DFFF',
            'OpenCoast': 'DEFF00',
            'Water': '0050D5',
            'NonMangroves': '106703',
            'Other': 'B06F03'
        }
        self.year_list = year_list
        self.class_list = classes_list
        self.size_mangroves = size_mangroves
        
        self.total_mean_carbon_per_year = mean_list
        self.total_stddev_carbon_per_year = stddev_list
        
        self.mean_carbon_per_class_year = mean_dict
        self.stddev_carbon_per_class_year = stddev_dict
        self.pixelCount_per_class_year = pixelCount_dict
        self.areaSqM_per_class_year = area_dict

